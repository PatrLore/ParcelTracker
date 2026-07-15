"""An IMAP mailbox a user has connected for shipping-confirmation import."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import MailAccountAuthType

if TYPE_CHECKING:
    from app.models.user import User


class MailAccount(Base, TimestampMixin):
    __tablename__ = "mail_accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    email_address: Mapped[str] = mapped_column(String(255), nullable=False)
    imap_host: Mapped[str] = mapped_column(String(255), nullable=False)
    imap_port: Mapped[int] = mapped_column(Integer, default=993, nullable=False)
    imap_username: Mapped[str] = mapped_column(String(255), nullable=False)
    auth_type: Mapped[str] = mapped_column(
        String(20), default=MailAccountAuthType.PASSWORD, nullable=False
    )
    #: Null for OAuth accounts (``auth_type == "oauth_microsoft"``), which
    #: authenticate with ``encrypted_oauth_refresh_token`` instead.
    encrypted_password: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    encrypted_oauth_refresh_token: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    use_ssl: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    folder: Mapped[str] = mapped_column(String(255), default="INBOX", nullable=False)
    use_idle: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    poll_interval_seconds: Mapped[int] = mapped_column(Integer, default=300, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    last_seen_uid: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship(back_populates="mail_accounts")
