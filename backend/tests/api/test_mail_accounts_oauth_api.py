"""API tests for the Microsoft OAuth device-code sign-in endpoints. The
device-flow HTTP calls themselves are tested in
tests/unit/test_oauth_microsoft.py; these tests stub that module to verify
request/response wiring and error-code mapping."""

from __future__ import annotations

import pytest

from app.config import MicrosoftOAuthSettings, Settings
from app.services.oauth_microsoft import (
    DeviceFlow,
    DeviceFlowExpiredError,
    DeviceFlowFailedError,
    DeviceFlowNotFoundError,
    TokenResult,
)


@pytest.fixture()
def auth_headers(client):
    client.post("/api/v1/users", json={"email": "oauth@example.com", "password": "password123"})
    login = client.post(
        "/api/v1/auth/login", json={"email": "oauth@example.com", "password": "password123"}
    )
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def _oauth_enabled(monkeypatch):
    settings = Settings(
        microsoft_oauth=MicrosoftOAuthSettings(enabled=True, client_id="test-client-id")
    )
    monkeypatch.setattr("app.api.v1.endpoints.mail_accounts.get_settings", lambda: settings)


def test_start_requires_authentication(client):
    response = client.post("/api/v1/mail-accounts/oauth/microsoft/start")
    assert response.status_code == 401


def test_start_returns_503_when_not_configured(client, auth_headers, monkeypatch):
    monkeypatch.setattr(
        "app.api.v1.endpoints.mail_accounts.get_settings",
        lambda: Settings(microsoft_oauth=MicrosoftOAuthSettings(enabled=False)),
    )

    response = client.post("/api/v1/mail-accounts/oauth/microsoft/start", headers=auth_headers)

    assert response.status_code == 503


def test_start_returns_user_code(client, auth_headers, monkeypatch):
    flow = DeviceFlow(
        flow_id="f1",
        user_id=1,
        device_code="dc-1",
        user_code="ABC-123",
        verification_uri="https://microsoft.com/devicelogin",
        expires_at=0.0,
        interval=5,
    )
    monkeypatch.setattr(
        "app.api.v1.endpoints.mail_accounts.start_device_flow", lambda client, user_id: flow
    )

    response = client.post("/api/v1/mail-accounts/oauth/microsoft/start", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["flow_id"] == "f1"
    assert body["user_code"] == "ABC-123"
    assert body["verification_uri"] == "https://microsoft.com/devicelogin"


def test_poll_returns_pending(client, auth_headers, monkeypatch):
    monkeypatch.setattr(
        "app.api.v1.endpoints.mail_accounts.poll_device_flow",
        lambda client, flow_id, user_id: False,
    )

    response = client.get("/api/v1/mail-accounts/oauth/microsoft/poll/f1", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == {"status": "pending"}


def test_poll_returns_complete(client, auth_headers, monkeypatch):
    monkeypatch.setattr(
        "app.api.v1.endpoints.mail_accounts.poll_device_flow",
        lambda client, flow_id, user_id: True,
    )

    response = client.get("/api/v1/mail-accounts/oauth/microsoft/poll/f1", headers=auth_headers)

    assert response.json() == {"status": "complete"}


def test_poll_maps_expired_to_408(client, auth_headers, monkeypatch):
    def raise_expired(client, flow_id, user_id):
        raise DeviceFlowExpiredError

    monkeypatch.setattr("app.api.v1.endpoints.mail_accounts.poll_device_flow", raise_expired)

    response = client.get("/api/v1/mail-accounts/oauth/microsoft/poll/f1", headers=auth_headers)

    assert response.status_code == 408


def test_poll_maps_not_found_to_404(client, auth_headers, monkeypatch):
    def raise_not_found(client, flow_id, user_id):
        raise DeviceFlowNotFoundError

    monkeypatch.setattr("app.api.v1.endpoints.mail_accounts.poll_device_flow", raise_not_found)

    response = client.get("/api/v1/mail-accounts/oauth/microsoft/poll/f1", headers=auth_headers)

    assert response.status_code == 404


def test_poll_maps_failed_to_400(client, auth_headers, monkeypatch):
    def raise_failed(client, flow_id, user_id):
        raise DeviceFlowFailedError("declined")

    monkeypatch.setattr("app.api.v1.endpoints.mail_accounts.poll_device_flow", raise_failed)

    response = client.get("/api/v1/mail-accounts/oauth/microsoft/poll/f1", headers=auth_headers)

    assert response.status_code == 400


def test_finalize_creates_oauth_account(client, auth_headers, monkeypatch):
    monkeypatch.setattr(
        "app.api.v1.endpoints.mail_accounts.take_completed_tokens",
        lambda flow_id, user_id: TokenResult(
            access_token="at-1", refresh_token="rt-1", expires_in=3600
        ),
    )

    response = client.post(
        "/api/v1/mail-accounts/oauth/microsoft/finalize",
        json={"flow_id": "f1", "email_address": "owner@hotmail.com"},
        headers=auth_headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["email_address"] == "owner@hotmail.com"
    assert body["auth_type"] == "oauth_microsoft"
    assert body["imap_host"] == "outlook.office365.com"
    assert "password" not in body
    assert "encrypted_oauth_refresh_token" not in body


def test_finalize_without_completed_flow_returns_404(client, auth_headers, monkeypatch):
    def raise_not_found(flow_id, user_id):
        raise DeviceFlowNotFoundError

    monkeypatch.setattr("app.api.v1.endpoints.mail_accounts.take_completed_tokens", raise_not_found)

    response = client.post(
        "/api/v1/mail-accounts/oauth/microsoft/finalize",
        json={"flow_id": "f1", "email_address": "owner@hotmail.com"},
        headers=auth_headers,
    )

    assert response.status_code == 404


def test_reconnect_updates_existing_account(client, auth_headers, monkeypatch):
    monkeypatch.setattr(
        "app.api.v1.endpoints.mail_accounts.take_completed_tokens",
        lambda flow_id, user_id: TokenResult(
            access_token="at-1", refresh_token="rt-2", expires_in=3600
        ),
    )
    create_response = client.post(
        "/api/v1/mail-accounts/oauth/microsoft/finalize",
        json={"flow_id": "f1", "email_address": "owner@hotmail.com"},
        headers=auth_headers,
    )
    account_id = create_response.json()["id"]

    monkeypatch.setattr(
        "app.api.v1.endpoints.mail_accounts.take_completed_tokens",
        lambda flow_id, user_id: TokenResult(
            access_token="at-2", refresh_token="rt-3", expires_in=3600
        ),
    )

    response = client.post(
        f"/api/v1/mail-accounts/{account_id}/oauth/microsoft/reconnect",
        json={"flow_id": "f2"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["id"] == account_id


def test_reconnect_unknown_account_returns_404(client, auth_headers, monkeypatch):
    monkeypatch.setattr(
        "app.api.v1.endpoints.mail_accounts.take_completed_tokens",
        lambda flow_id, user_id: TokenResult(
            access_token="at-1", refresh_token="rt-2", expires_in=3600
        ),
    )

    response = client.post(
        "/api/v1/mail-accounts/999999/oauth/microsoft/reconnect",
        json={"flow_id": "f1"},
        headers=auth_headers,
    )

    assert response.status_code == 404
