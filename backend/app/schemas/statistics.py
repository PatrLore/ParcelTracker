"""Statistics summary schema (Phase 5)."""

from __future__ import annotations

from pydantic import BaseModel


class MonthlyCount(BaseModel):
    month: str  # "YYYY-MM"
    count: int


class StatisticsSummary(BaseModel):
    parcels_per_month: list[MonthlyCount]
    average_delivery_days: float | None
    top_merchant: str | None
    top_carrier: str | None
    delayed_rate: float
    success_rate: float | None
    total_shipments: int
