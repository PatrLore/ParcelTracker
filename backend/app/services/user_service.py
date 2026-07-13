"""User management business logic."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate
from app.services.exceptions import AlreadyExistsError, NotFoundError


class UserService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)

    def create_user(self, data: UserCreate, *, is_superuser: bool = False) -> User:
        if self.users.get_by_email(data.email) is not None:
            raise AlreadyExistsError(f"User with email {data.email} already exists")
        user = User(
            email=data.email,
            full_name=data.full_name,
            hashed_password=hash_password(data.password),
            is_superuser=is_superuser,
        )
        user = self.users.add(user)
        self.users.commit()
        return user

    def get_user(self, user_id: int) -> User:
        user = self.users.get(user_id)
        if user is None:
            raise NotFoundError(f"User {user_id} not found")
        return user
