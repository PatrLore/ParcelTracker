"""Shipping carrier reference data (DHL, UPS, DPD, ...)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.shipment import Shipment


class Carrier(Base, TimestampMixin):
    __tablename__ = "carriers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    api_identifier: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tracking_url_template: Mapped[str | None] = mapped_column(String(500), nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    shipments: Mapped[list[Shipment]] = relationship(back_populates="carrier")
