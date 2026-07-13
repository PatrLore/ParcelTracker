"""Data access for :class:`~app.models.mail_account.MailAccount`."""

from __future__ import annotations

from sqlalchemy import select

from app.models.mail_account import MailAccount
from app.repositories.base import BaseRepository


class MailAccountRepository(BaseRepository[MailAccount]):
    model = MailAccount

    def list_for_user(self, user_id: int) -> list[MailAccount]:
        stmt = select(MailAccount).where(MailAccount.user_id == user_id)
        return list(self.db.scalars(stmt).all())

    def get_for_user(self, mail_account_id: int, user_id: int) -> MailAccount | None:
        stmt = select(MailAccount).where(
            MailAccount.id == mail_account_id, MailAccount.user_id == user_id
        )
        return self.db.scalars(stmt).first()

    def list_active(self) -> list[MailAccount]:
        """All active mail accounts across every user - used by the import worker."""
        stmt = select(MailAccount).where(MailAccount.is_active.is_(True))
        return list(self.db.scalars(stmt).all())
