"""Shipment and tracking-event schemas."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import ShipmentStatus
from app.schemas.carrier import CarrierRead


class TrackingEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: ShipmentStatus
    description: str | None
    location: str | None
    occurred_at: datetime


class ShipmentBase(BaseModel):
    tracking_number: str
    carrier_id: int | None = None
    tracking_status: ShipmentStatus = ShipmentStatus.UNKNOWN
    ship_date: date | None = None
    estimated_delivery_date: date | None = None
    delivery_date: date | None = None


class ShipmentCreate(ShipmentBase):
    order_id: int | None = None


class ShipmentUpdate(BaseModel):
    tracking_status: ShipmentStatus | None = None
    estimated_delivery_date: date | None = None
    delivery_date: date | None = None


class ShipmentRead(ShipmentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: int | None
    last_update: datetime | None
    carrier: CarrierRead | None = None
    tracking_events: list[TrackingEventRead] = []
