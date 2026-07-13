"""Data access for :class:`~app.models.carrier.Carrier`."""

from __future__ import annotations

from sqlalchemy import select

from app.models.carrier import Carrier
from app.repositories.base import BaseRepository


class CarrierRepository(BaseRepository[Carrier]):
    model = Carrier

    def get_by_name(self, name: str) -> Carrier | None:
        stmt = select(Carrier).where(Carrier.name == name)
        return self.db.scalars(stmt).first()
