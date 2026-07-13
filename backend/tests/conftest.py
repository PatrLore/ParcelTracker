"""Shared pytest fixtures: isolated in-memory database and API test client."""

from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import get_db
from app.main import app as fastapi_app
from app.models.base import Base


@pytest.fixture()
def engine():
    eng = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)
    eng.dispose()


@pytest.fixture()
def db_session(engine) -> Generator[Session]:
    testing_session_local = sessionmaker(
        bind=engine, autocommit=False, autoflush=False, future=True
    )
    session = testing_session_local()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(engine) -> Generator[TestClient]:
    testing_session_local = sessionmaker(
        bind=engine, autocommit=False, autoflush=False, future=True
    )

    def override_get_db() -> Generator[Session]:
        session = testing_session_local()
        try:
            yield session
        finally:
            session.close()

    fastapi_app.dependency_overrides[get_db] = override_get_db
    with TestClient(fastapi_app) as test_client:
        yield test_client
    fastapi_app.dependency_overrides.clear()
