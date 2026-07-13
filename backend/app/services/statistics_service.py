"""Aggregated statistics (Phase 5): parcels per month, average delivery
time, top merchant/carrier, delay rate, success rate."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.repositories.order_repository import OrderRepository
from app.repositories.shipment_repository import ShipmentRepository
from app.schemas.statistics import MonthlyCount, StatisticsSummary


class StatisticsService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.orders = OrderRepository(db)
        self.shipments = ShipmentRepository(db)

    def get_summary(self, user_id: int, months: int = 12) -> StatisticsSummary:
        monthly_counts = self.orders.monthly_counts_for_user(user_id, months=months)
        durations = self.shipments.delivery_durations_for_user(user_id)
        delivered, returned = self.shipments.terminal_counts_for_user(user_id)
        total_shipments = self.shipments.count_for_user(user_id)
        delayed = self.shipments.delayed_shipment_count_for_user(user_id)
        terminal_total = delivered + returned

        return StatisticsSummary(
            parcels_per_month=[
                MonthlyCount(month=month, count=count) for month, count in monthly_counts
            ],
            average_delivery_days=(
                round(sum(durations) / len(durations), 1) if durations else None
            ),
            top_merchant=self.orders.top_merchant_for_user(user_id),
            top_carrier=self.shipments.top_carrier_for_user(user_id),
            delayed_rate=round(delayed / total_shipments, 3) if total_shipments else 0.0,
            success_rate=round(delivered / terminal_total, 3) if terminal_total else None,
            total_shipments=total_shipments,
        )
