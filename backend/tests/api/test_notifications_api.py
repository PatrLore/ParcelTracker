"""API tests for the manual notification-send endpoint."""

from __future__ import annotations

import pytest

from app.config import Settings


@pytest.fixture()
def auth_headers(client):
    client.post(
        "/api/v1/users", json={"email": "notify-api@example.com", "password": "password123"}
    )
    login = client.post(
        "/api/v1/auth/login", json={"email": "notify-api@example.com", "password": "password123"}
    )
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_send_notification_with_no_channels_configured(client, auth_headers, monkeypatch):
    monkeypatch.setattr(
        "app.services.notification_dispatch_factory.get_settings", lambda: Settings()
    )

    response = client.post(
        "/api/v1/notifications/send",
        json={"title": "Parcel delivered", "body": "Your parcel arrived."},
        headers=auth_headers,
    )

    assert response.status_code == 202
    assert response.json() == {"dispatched": True, "channel_count": 0}


def test_send_notification_requires_authentication(client):
    response = client.post("/api/v1/notifications/send", json={"title": "Hi", "body": "Body"})
    assert response.status_code == 401
