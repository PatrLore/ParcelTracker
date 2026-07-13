"""Raw shipping-confirmation emails ingested by the IMAP importer (Phase 2)."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.order import Order


class Email(Base, TimestampMixin):
    __tablename__ = "emails"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int | None] = mapped_column(
        ForeignKey("orders.id", ondelete="SET NULL"), nullable=True, index=True
    )

    message_id: Mapped[str] = mapped_column(String(998), unique=True, index=True, nullable=False)
    subject: Mapped[str | None] = mapped_column(String(998), nullable=True)
    sender: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    raw_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    attachments: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)

    order: Mapped[Order | None] = relationship()
