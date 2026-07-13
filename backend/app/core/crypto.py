"""Symmetric encryption for secrets stored at rest (e.g. IMAP passwords).

Kept separate from ``security.py`` (which handles user-facing auth) because
this protects *our* credentials to third-party systems, not user sessions.
"""

from __future__ import annotations

from functools import lru_cache

from cryptography.fernet import Fernet

from app.config import get_settings


@lru_cache
def _fernet() -> Fernet:
    key = get_settings().security.mail_encryption_key
    return Fernet(key.encode())


def encrypt_secret(plain_text: str) -> str:
    return _fernet().encrypt(plain_text.encode()).decode()


def decrypt_secret(token: str) -> str:
    return _fernet().decrypt(token.encode()).decode()
