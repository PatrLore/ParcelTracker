"""Order placed with a merchant, optionally linked to one or more shipments."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import OrderStatus

if TYPE_CHECKING:
    from app.models.shipment import Shipment
    from app.models.user import User


class Order(Base, TimestampMixin):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    merchant: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    order_number: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    order_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    invoice_amount: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="EUR", nullable=False)
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, native_enum=False), default=OrderStatus.PENDING, nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped[User] = relationship(back_populates="orders")
    shipments: Mapped[list[Shipment]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )
