"""Authentication business logic: credential checks and token issuance."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.security import create_access_token, create_refresh_token, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import TokenResponse
from app.services.exceptions import InvalidCredentialsError


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)

    def authenticate(self, email: str, password: str) -> User:
        user = self.users.get_by_email(email)
        if user is None or not verify_password(password, user.hashed_password):
            raise InvalidCredentialsError("Invalid email or password")
        if not user.is_active:
            raise InvalidCredentialsError("User account is disabled")
        return user

    def login(self, email: str, password: str) -> TokenResponse:
        user = self.authenticate(email, password)
        return TokenResponse(
            access_token=create_access_token(str(user.id)),
            refresh_token=create_refresh_token(str(user.id)),
        )
