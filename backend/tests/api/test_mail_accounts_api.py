"""API tests for mail account CRUD (fetch/parse/persist behavior during a
sync is covered at the service level, since it requires a real or faked
IMAP connection - see tests/unit/test_email_ingestion_service.py). The
tests below only check that the sync endpoint logs its result, so it's
traceable in the log file even when a manual "Sync now" click was missed
in the UI."""

from __future__ import annotations

import logging

import pytest

from app.schemas.mail_account import MailAccountSyncResult


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


def test_sync_logs_result_on_success(client, auth_headers, monkeypatch, caplog):
    account_id = client.post("/api/v1/mail-accounts", json=_payload(), headers=auth_headers).json()[
        "id"
    ]

    class StubIngestionService:
        def __init__(self, db):
            pass

        def sync_account(self, account):
            return MailAccountSyncResult(fetched_emails=2, matched_orders=1, created_shipments=1)

    monkeypatch.setattr(
        "app.api.v1.endpoints.mail_accounts.EmailIngestionService", StubIngestionService
    )

    with caplog.at_level(logging.INFO, logger="app.api.v1.endpoints.mail_accounts"):
        response = client.post(f"/api/v1/mail-accounts/{account_id}/sync", headers=auth_headers)

    assert response.status_code == 200
    assert (
        "Synced me@gmail.com (manual): 2 new email(s), 1 matched order(s), 1 new shipment(s)"
        in caplog.text
    )


def test_sync_logs_warning_on_connection_error(client, auth_headers, monkeypatch, caplog):
    account_id = client.post("/api/v1/mail-accounts", json=_payload(), headers=auth_headers).json()[
        "id"
    ]

    class StubIngestionService:
        def __init__(self, db):
            pass

        def sync_account(self, account):
            raise ConnectionError("mailbox unreachable")

    monkeypatch.setattr(
        "app.api.v1.endpoints.mail_accounts.EmailIngestionService", StubIngestionService
    )

    with caplog.at_level(logging.WARNING, logger="app.api.v1.endpoints.mail_accounts"):
        response = client.post(f"/api/v1/mail-accounts/{account_id}/sync", headers=auth_headers)

    assert response.status_code == 502
    assert "Manual sync failed for me@gmail.com: mailbox unreachable" in caplog.text
