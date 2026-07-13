"""Order business logic."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.order import Order
from app.repositories.order_repository import OrderRepository
from app.schemas.order import OrderCreate, OrderUpdate
from app.services.exceptions import NotFoundError


class OrderService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.orders = OrderRepository(db)

    def list_orders(self, user_id: int, offset: int = 0, limit: int = 100) -> list[Order]:
        return self.orders.list_for_user(user_id, offset=offset, limit=limit)

    def get_order(self, order_id: int, user_id: int) -> Order:
        order = self.orders.get_for_user(order_id, user_id)
        if order is None:
            raise NotFoundError(f"Order {order_id} not found")
        return order

    def create_order(self, data: OrderCreate, user_id: int) -> Order:
        order = Order(**data.model_dump(), user_id=user_id)
        order = self.orders.add(order)
        self.orders.commit()
        return order

    def update_order(self, order_id: int, data: OrderUpdate, user_id: int) -> Order:
        order = self.get_order(order_id, user_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(order, field, value)
        self.orders.commit()
        self.db.refresh(order)
        return order

    def delete_order(self, order_id: int, user_id: int) -> None:
        order = self.get_order(order_id, user_id)
        self.orders.delete(order)
        self.orders.commit()
