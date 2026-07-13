"""Unit tests for the user service layer."""

from __future__ import annotations

import pytest

from app.schemas.user import UserCreate
from app.services.exceptions import AlreadyExistsError, NotFoundError
from app.services.user_service import UserService


def test_create_user_hashes_password(db_session):
    service = UserService(db_session)
    user = service.create_user(UserCreate(email="a@example.com", password="password123"))

    assert user.id is not None
    assert user.hashed_password != "password123"


def test_create_user_rejects_duplicate_email(db_session):
    service = UserService(db_session)
    service.create_user(UserCreate(email="dup@example.com", password="password123"))

    with pytest.raises(AlreadyExistsError):
        service.create_user(UserCreate(email="dup@example.com", password="otherpassword"))


def test_get_user_raises_when_missing(db_session):
    service = UserService(db_session)
    with pytest.raises(NotFoundError):
        service.get_user(999)
