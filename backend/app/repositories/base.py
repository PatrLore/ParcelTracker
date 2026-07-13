"""Generic repository providing common CRUD operations for any ORM model."""

from __future__ import annotations

from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Thin data-access layer isolating the service layer from SQLAlchemy details."""

    model: type[ModelType]

    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, id_: int) -> ModelType | None:
        return self.db.get(self.model, id_)

    def list(self, offset: int = 0, limit: int = 100) -> list[ModelType]:
        stmt = select(self.model).offset(offset).limit(limit)
        return list(self.db.scalars(stmt).all())

    def add(self, instance: ModelType) -> ModelType:
        self.db.add(instance)
        self.db.flush()
        self.db.refresh(instance)
        return instance

    def delete(self, instance: ModelType) -> None:
        self.db.delete(instance)
        self.db.flush()

    def commit(self) -> None:
        self.db.commit()
