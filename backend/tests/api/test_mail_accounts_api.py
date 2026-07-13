"""API tests for mail account CRUD (sync is covered at the service level,
since it requires a real or faked IMAP connection - see
tests/unit/test_email_ingestion_service.py)."""

from __future__ import annotations

import pytest


@pytest.fixture()
def auth_headers(client):
    client.post("/api/v1/users", json={"email": "mailboxes@example.com", "password": "password123"})
    login = client.post(
        "/api/v1/auth/login", json={"email": "mailboxes@example.com", "password": "password123"}
    )
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _payload(**overrides):
    fields = {
        "email_address": "me@gmail.com",
        "imap_host": "imap.gmail.com",
        "imap_username": "me@gmail.com",
        "password": "app-password",
    }
    fields.update(overrides)
    return fields


def test_create_mail_account_never_returns_password(client, auth_headers):
    response = client.post("/api/v1/mail-accounts", json=_payload(), headers=auth_headers)

    assert response.status_code == 201
    body = response.json()
    assert "password" not in body
    assert "encrypted_password" not in body
    assert body["email_address"] == "me@gmail.com"


def test_list_and_get_mail_account(client, auth_headers):
    create_response = client.post("/api/v1/mail-accounts", json=_payload(), headers=auth_headers)
    account_id = create_response.json()["id"]

    list_response = client.get("/api/v1/mail-accounts", headers=auth_headers)
    assert list_response.status_code == 200
    assert any(account["id"] == account_id for account in list_response.json())

    get_response = client.get(f"/api/v1/mail-accounts/{account_id}", headers=auth_headers)
    assert get_response.status_code == 200


def test_update_and_delete_mail_account(client, auth_headers):
    create_response = client.post("/api/v1/mail-accounts", json=_payload(), headers=auth_headers)
    account_id = create_response.json()["id"]

    update_response = client.patch(
        f"/api/v1/mail-accounts/{account_id}", json={"is_active": False}, headers=auth_headers
    )
    assert update_response.status_code == 200
    assert update_response.json()["is_active"] is False

    delete_response = client.delete(f"/api/v1/mail-accounts/{account_id}", headers=auth_headers)
    assert delete_response.status_code == 204

    get_response = client.get(f"/api/v1/mail-accounts/{account_id}", headers=auth_headers)
    assert get_response.status_code == 404


def test_mail_accounts_require_authentication(client):
    response = client.get("/api/v1/mail-accounts")
    assert response.status_code == 401
