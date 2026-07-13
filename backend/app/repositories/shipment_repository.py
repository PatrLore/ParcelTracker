"""Data access for :class:`~app.models.shipment.Shipment`."""

from __future__ import annotations

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import joinedload

from app.models.carrier import Carrier
from app.models.enums import ShipmentStatus
from app.models.order import Order
from app.models.shipment import Shipment, TrackingEvent
from app.repositories.base import BaseRepository

#: Shipments in one of these statuses are done - no need to keep polling
#: the tracking provider for them.
TERMINAL_STATUSES = (ShipmentStatus.DELIVERED, ShipmentStatus.RETURNED)


class ShipmentRepository(BaseRepository[Shipment]):
    model = Shipment

    def get_for_user(self, shipment_id: int, user_id: int) -> Shipment | None:
        stmt = (
            self._base_user_query(user_id)
            .where(Shipment.id == shipment_id)
            .options(joinedload(Shipment.carrier), joinedload(Shipment.tracking_events))
        )
        return self.db.scalars(stmt).unique().first()

    def list_for_user(self, user_id: int, offset: int = 0, limit: int = 100) -> list[Shipment]:
        stmt = (
            select(Shipment)
            .join(Order, Shipment.order_id == Order.id)
            .where(Order.user_id == user_id)
            .options(joinedload(Shipment.carrier), joinedload(Shipment.tracking_events))
            .offset(offset)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).unique().all())

    def get_by_order_and_tracking_number(
        self, order_id: int, tracking_number: str
    ) -> Shipment | None:
        stmt = select(Shipment).where(
            Shipment.order_id == order_id, Shipment.tracking_number == tracking_number
        )
        return self.db.scalars(stmt).first()

    def list_non_terminal(self) -> list[Shipment]:
        """All shipments (across every user) not yet delivered/returned -
        used by the tracking-refresh worker."""
        stmt = (
            select(Shipment)
            .where(Shipment.tracking_status.notin_(TERMINAL_STATUSES))
            .options(joinedload(Shipment.carrier), joinedload(Shipment.tracking_events))
        )
        return list(self.db.scalars(stmt).unique().all())

    def count_all(self) -> int:
        """Shipment count across every user - used by the MQTT sensor publisher."""
        return self.db.scalar(select(func.count()).select_from(Shipment)) or 0

    def count_all_by_status(self, status: ShipmentStatus) -> int:
        stmt = select(func.count()).select_from(
            select(Shipment).where(Shipment.tracking_status == status).subquery()
        )
        return self.db.scalar(stmt) or 0

    def count_all_delivered_on(self, day: date) -> int:
        stmt = select(func.count()).select_from(
            select(Shipment).where(Shipment.delivery_date == day).subquery()
        )
        return self.db.scalar(stmt) or 0

    def next_delivery_date(self) -> date | None:
        stmt = (
            select(Shipment.estimated_delivery_date)
            .where(Shipment.estimated_delivery_date.isnot(None))
            .where(Shipment.tracking_status.notin_(TERMINAL_STATUSES))
            .order_by(Shipment.estimated_delivery_date.asc())
            .limit(1)
        )
        return self.db.scalar(stmt)

    def _base_user_query(self, user_id: int, exclude_archived: bool = False):
        stmt = (
            select(Shipment)
            .join(Order, Shipment.order_id == Order.id)
            .where(Order.user_id == user_id)
        )
        if exclude_archived:
            stmt = stmt.where(Order.archived.is_(False))
        return stmt

    def count_by_status(
        self, user_id: int, status: ShipmentStatus, exclude_archived: bool = False
    ) -> int:
        stmt = self._base_user_query(user_id, exclude_archived).where(
            Shipment.tracking_status == status
        )
        return self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0

    def count_delivered_on(self, user_id: int, day: date, exclude_archived: bool = False) -> int:
        stmt = self._base_user_query(user_id, exclude_archived).where(Shipment.delivery_date == day)
        return self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0

    def count_expected_on(self, user_id: int, day: date, exclude_archived: bool = False) -> int:
        stmt = self._base_user_query(user_id, exclude_archived).where(
            Shipment.estimated_delivery_date == day
        )
        return self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0

    def recent(
        self, user_id: int, limit: int = 10, exclude_archived: bool = False
    ) -> list[Shipment]:
        stmt = (
            self._base_user_query(user_id, exclude_archived)
            .options(joinedload(Shipment.carrier), joinedload(Shipment.tracking_events))
            .order_by(Shipment.updated_at.desc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt).unique().all())

    def count_for_user(self, user_id: int) -> int:
        stmt = self._base_user_query(user_id)
        return self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0

    def top_carrier_for_user(self, user_id: int) -> str | None:
        stmt = (
            select(Carrier.name, func.count().label("count"))
            .select_from(Shipment)
            .join(Order, Shipment.order_id == Order.id)
            .join(Carrier, Shipment.carrier_id == Carrier.id)
            .where(Order.user_id == user_id)
            .group_by(Carrier.name)
            .order_by(func.count().desc())
            .limit(1)
        )
        row = self.db.execute(stmt).first()
        return row[0] if row else None

    def delayed_shipment_count_for_user(self, user_id: int) -> int:
        """Shipments currently DELAYED, or that had a DELAYED event at some
        point in their history (even if since resolved)."""
        currently_delayed = (
            select(Shipment.id)
            .select_from(Shipment)
            .join(Order, Shipment.order_id == Order.id)
            .where(Order.user_id == user_id, Shipment.tracking_status == ShipmentStatus.DELAYED)
        )
        ever_delayed = (
            select(Shipment.id)
            .select_from(Shipment)
            .join(Order, Shipment.order_id == Order.id)
            .join(TrackingEvent, TrackingEvent.shipment_id == Shipment.id)
            .where(Order.user_id == user_id, TrackingEvent.status == ShipmentStatus.DELAYED)
        )
        combined = currently_delayed.union(ever_delayed).subquery()
        return self.db.scalar(select(func.count()).select_from(combined)) or 0

    def terminal_counts_for_user(self, user_id: int) -> tuple[int, int]:
        """``(delivered_count, returned_count)`` for the success-rate statistic."""
        return (
            self.count_by_status(user_id, ShipmentStatus.DELIVERED),
            self.count_by_status(user_id, ShipmentStatus.RETURNED),
        )

    def delivery_durations_for_user(self, user_id: int) -> list[int]:
        """Days from order date (or order creation, if unset) to delivery,
        for every delivered shipment - the raw data for an average delivery
        time statistic."""
        stmt = (
            select(Order.order_date, Order.created_at, Shipment.delivery_date)
            .select_from(Shipment)
            .join(Order, Shipment.order_id == Order.id)
            .where(Order.user_id == user_id, Shipment.delivery_date.isnot(None))
        )
        durations = []
        for order_date, created_at, delivery_date in self.db.execute(stmt).all():
            start = order_date or created_at.date()
            durations.append((delivery_date - start).days)
        return durations
