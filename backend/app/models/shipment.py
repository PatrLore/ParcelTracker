"""Shipment/parcel and its tracking history."""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import ShipmentStatus

if TYPE_CHECKING:
    from app.models.carrier import Carrier
    from app.models.order import Order


class Shipment(Base, TimestampMixin):
    __tablename__ = "shipments"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int | None] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), nullable=True, index=True
    )
    carrier_id: Mapped[int | None] = mapped_column(
        ForeignKey("carriers.id", ondelete="SET NULL"), nullable=True, index=True
    )

    tracking_number: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    tracking_status: Mapped[ShipmentStatus] = mapped_column(
        Enum(ShipmentStatus, native_enum=False), default=ShipmentStatus.UNKNOWN, nullable=False
    )
    ship_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    estimated_delivery_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    delivery_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    last_update: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    #: Whether register() has already been called against the configured
    #: TrackingProvider for this shipment (Phase 3) - avoids re-registering
    #: on every sync.
    tracking_registered: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    order: Mapped[Order] = relationship(back_populates="shipments")
    carrier: Mapped[Carrier] = relationship(back_populates="shipments")
    tracking_events: Mapped[list[TrackingEvent]] = relationship(
        back_populates="shipment",
        cascade="all, delete-orphan",
        order_by="TrackingEvent.occurred_at",
    )


class TrackingEvent(Base, TimestampMixin):
    """A single status update in a shipment's tracking history."""

    __tablename__ = "tracking_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    shipment_id: Mapped[int] = mapped_column(
        ForeignKey("shipments.id", ondelete="CASCADE"), nullable=False, index=True
    )

    status: Mapped[ShipmentStatus] = mapped_column(
        Enum(ShipmentStatus, native_enum=False), nullable=False
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    shipment: Mapped[Shipment] = relationship(back_populates="tracking_events")
