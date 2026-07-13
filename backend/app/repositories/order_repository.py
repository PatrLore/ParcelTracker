"""Data access for :class:`~app.models.order.Order`."""

from __future__ import annotations

from datetime import date

from sqlalchemy import func, select

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

    def get_by_merchant_and_number(
        self, user_id: int, merchant: str, order_number: str
    ) -> Order | None:
        stmt = select(Order).where(
            Order.user_id == user_id,
            Order.merchant == merchant,
            Order.order_number == order_number,
        )
        return self.db.scalars(stmt).first()

    def monthly_counts_for_user(self, user_id: int, months: int = 12) -> list[tuple[str, int]]:
        """Order counts per calendar month for the last ``months`` months,
        oldest first, including months with zero orders.

        Bucketed in Python rather than with a SQL date-trunc function so the
        query stays portable across SQLite/PostgreSQL/MariaDB.
        """
        today = date.today()
        first_month_ordinal = today.year * 12 + (today.month - 1) - (months - 1)

        counts: dict[str, int] = {}
        for offset in range(months):
            year, month0 = divmod(first_month_ordinal + offset, 12)
            counts[f"{year:04d}-{month0 + 1:02d}"] = 0

        year, month0 = divmod(first_month_ordinal, 12)
        start_date = date(year, month0 + 1, 1)

        stmt = select(Order.created_at).where(
            Order.user_id == user_id, Order.created_at >= start_date
        )
        for created_at in self.db.scalars(stmt).all():
            key = f"{created_at.year:04d}-{created_at.month:02d}"
            if key in counts:
                counts[key] += 1

        return list(counts.items())

    def top_merchant_for_user(self, user_id: int) -> str | None:
        stmt = (
            select(Order.merchant, func.count().label("count"))
            .where(Order.user_id == user_id)
            .group_by(Order.merchant)
            .order_by(func.count().desc())
            .limit(1)
        )
        row = self.db.execute(stmt).first()
        return row[0] if row else None
