"""Data access for :class:`~app.models.order.Order`."""

from __future__ import annotations

from sqlalchemy import select

from app.models.order import Order
from app.repositories.base import BaseRepository


class OrderRepository(BaseRepository[Order]):
    model = Order

    def list_for_user(self, user_id: int, offset: int = 0, limit: int = 100) -> list[Order]:
        stmt = select(Order).where(Order.user_id == user_id).offset(offset).limit(limit)
        return list(self.db.scalars(stmt).all())

    def get_for_user(self, order_id: int, user_id: int) -> Order | None:
        stmt = select(Order).where(Order.id == order_id, Order.user_id == user_id)
        return self.db.scalars(stmt).first()
