"""Aggregates shipment data into the dashboard summary shown on the homepage."""

from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.models.enums import ShipmentStatus
from app.repositories.shipment_repository import ShipmentRepository
from app.schemas.dashboard import DashboardSummary


class DashboardService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.shipments = ShipmentRepository(db)

    def get_summary(self, user_id: int, today: date | None = None) -> DashboardSummary:
        today = today or date.today()
        tomorrow = today + timedelta(days=1)

        in_transit = self.shipments.count_by_status(
            user_id, ShipmentStatus.IN_TRANSIT, exclude_archived=True
        ) + self.shipments.count_by_status(
            user_id, ShipmentStatus.OUT_FOR_DELIVERY, exclude_archived=True
        )
        delayed = self.shipments.count_by_status(
            user_id, ShipmentStatus.DELAYED, exclude_archived=True
        )
        delivered_today = self.shipments.count_delivered_on(user_id, today, exclude_archived=True)
        expected_tomorrow = self.shipments.count_expected_on(
            user_id, tomorrow, exclude_archived=True
        )
        new_confirmations = self.shipments.count_by_status(
            user_id, ShipmentStatus.LABEL_CREATED, exclude_archived=True
        )

        return DashboardSummary(
            in_transit=in_transit,
            delivered_today=delivered_today,
            expected_tomorrow=expected_tomorrow,
            delayed=delayed,
            new_confirmations=new_confirmations,
            recent_shipments=self.shipments.recent(user_id, exclude_archived=True),
        )
