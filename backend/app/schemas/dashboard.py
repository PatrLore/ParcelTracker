"""Dashboard summary schema."""

from __future__ import annotations

from pydantic import BaseModel

from app.schemas.shipment import ShipmentRead


class DashboardSummary(BaseModel):
    in_transit: int
    delivered_today: int
    expected_tomorrow: int
    delayed: int
    new_confirmations: int
    recent_shipments: list[ShipmentRead] = []
