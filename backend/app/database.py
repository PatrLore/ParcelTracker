"""Database engine/session management.

Kept driver-agnostic on purpose: swapping ``database.driver`` in ``config.yaml``
between sqlite, postgresql and mariadb requires no code changes here.
"""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings
from app.models.base import Base


def _build_engine():
    settings = get_settings()
    url = settings.database.sqlalchemy_url
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, connect_args=connect_args, future=True)


engine = _build_engine()
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


def init_db() -> None:
    """Create all tables. Used for tests/dev; production uses Alembic migrations."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session]:
    """FastAPI dependency yielding a request-scoped database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
