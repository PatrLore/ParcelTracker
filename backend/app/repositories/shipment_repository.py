"""Data access for :class:`~app.models.shipment.Shipment`."""

from __future__ import annotations

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import joinedload

from app.models.enums import ShipmentStatus
from app.models.order import Order
from app.models.shipment import Shipment
from app.repositories.base import BaseRepository


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

    def _base_user_query(self, user_id: int):
        return (
            select(Shipment)
            .join(Order, Shipment.order_id == Order.id)
            .where(Order.user_id == user_id)
        )

    def count_by_status(self, user_id: int, status: ShipmentStatus) -> int:
        stmt = self._base_user_query(user_id).where(Shipment.tracking_status == status)
        return self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0

    def count_delivered_on(self, user_id: int, day: date) -> int:
        stmt = self._base_user_query(user_id).where(Shipment.delivery_date == day)
        return self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0

    def count_expected_on(self, user_id: int, day: date) -> int:
        stmt = self._base_user_query(user_id).where(Shipment.estimated_delivery_date == day)
        return self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0

    def recent(self, user_id: int, limit: int = 10) -> list[Shipment]:
        stmt = (
            self._base_user_query(user_id)
            .options(joinedload(Shipment.carrier), joinedload(Shipment.tracking_events))
            .order_by(Shipment.updated_at.desc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt).unique().all())
