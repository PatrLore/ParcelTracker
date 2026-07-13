"""Order schemas."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.models.enums import OrderStatus
from app.schemas.shipment import ShipmentRead


class OrderBase(BaseModel):
    merchant: str
    order_number: str | None = None
    order_date: date | None = None
    invoice_amount: Decimal | None = None
    currency: str = "EUR"
    status: OrderStatus = OrderStatus.PENDING
    notes: str | None = None


class OrderCreate(OrderBase):
    pass


class OrderUpdate(BaseModel):
    merchant: str | None = None
    order_number: str | None = None
    order_date: date | None = None
    invoice_amount: Decimal | None = None
    currency: str | None = None
    status: OrderStatus | None = None
    notes: str | None = None


class OrderRead(OrderBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    archived: bool = False
    created_at: datetime
    updated_at: datetime
    shipments: list[ShipmentRead] = []


class OrderArchiveRequest(BaseModel):
    archived: bool = True
