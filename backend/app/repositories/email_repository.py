"""Data access for :class:`~app.models.email.Email`."""

from __future__ import annotations

from sqlalchemy import select

from app.models.email import Email
from app.repositories.base import BaseRepository


class EmailRepository(BaseRepository[Email]):
    model = Email

    def get_by_message_id(self, message_id: str) -> Email | None:
        stmt = select(Email).where(Email.message_id == message_id)
        return self.db.scalars(stmt).first()
