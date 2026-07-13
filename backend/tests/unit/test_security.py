"""Unit tests for password hashing and JWT helpers."""

from __future__ import annotations

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_hash_password_produces_verifiable_hash():
    hashed = hash_password("s3cret-passphrase")
    assert hashed != "s3cret-passphrase"
    assert verify_password("s3cret-passphrase", hashed)
    assert not verify_password("wrong-passphrase", hashed)


def test_access_token_round_trip():
    token = create_access_token(subject="42")
    payload = decode_token(token)
    assert payload is not None
    assert payload["sub"] == "42"
    assert payload["type"] == "access"


def test_refresh_token_round_trip():
    token = create_refresh_token(subject="7")
    payload = decode_token(token)
    assert payload is not None
    assert payload["sub"] == "7"
    assert payload["type"] == "refresh"


def test_decode_token_rejects_garbage():
    assert decode_token("not-a-real-token") is None
