"""Tests for the Google device-code OAuth2 flow. Uses httpx.MockTransport -
no real network calls - matching the convention in
tracking/tests/test_providers.py and test_version_service.py."""

from __future__ import annotations

import httpx
import pytest

from app.config import GoogleOAuthSettings, Settings
from app.services import oauth_google


def _client_with(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


@pytest.fixture(autouse=True)
def _configured_settings(monkeypatch):
    settings = Settings(
        google_oauth=GoogleOAuthSettings(
            enabled=True, client_id="test-client-id", client_secret="test-client-secret"
        )
    )
    monkeypatch.setattr(oauth_google, "get_settings", lambda: settings)
    yield
    oauth_google._pending_flows.clear()
    oauth_google._completed_flows.clear()


def test_start_device_flow_normalizes_verification_url():
    def handler(request: httpx.Request) -> httpx.Response:
        assert "device/code" in str(request.url)
        return httpx.Response(
            200,
            json={
                "device_code": "dc-1",
                "user_code": "ABC-123",
                "verification_url": "https://www.google.com/device",
                "expires_in": 1800,
                "interval": 5,
            },
        )

    flow = oauth_google.start_device_flow(_client_with(handler), user_id=7)

    assert flow.user_code == "ABC-123"
    assert flow.verification_uri == "https://www.google.com/device"
    assert flow.user_id == 7
    assert oauth_google._pending_flows[flow.flow_id] is flow


def test_poll_device_flow_pending_while_authorization_pending():
    flow = oauth_google.DeviceFlow(
        flow_id="f1",
        user_id=1,
        device_code="dc-1",
        user_code="ABC-123",
        verification_uri="https://www.google.com/device",
        expires_at=oauth_google.time.monotonic() + 900,
        interval=5,
    )
    oauth_google._pending_flows["f1"] = flow

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={"error": "authorization_pending"})

    complete = oauth_google.poll_device_flow(_client_with(handler), "f1", user_id=1)

    assert complete is False
    assert "f1" in oauth_google._pending_flows


def test_poll_device_flow_completes_and_caches_tokens():
    flow = oauth_google.DeviceFlow(
        flow_id="f2",
        user_id=1,
        device_code="dc-1",
        user_code="ABC-123",
        verification_uri="https://www.google.com/device",
        expires_at=oauth_google.time.monotonic() + 900,
        interval=5,
    )
    oauth_google._pending_flows["f2"] = flow

    def handler(request: httpx.Request) -> httpx.Response:
        assert "client_secret=test-client-secret" in request.content.decode()
        return httpx.Response(
            200,
            json={"access_token": "at-1", "refresh_token": "rt-1", "expires_in": 3600},
        )

    complete = oauth_google.poll_device_flow(_client_with(handler), "f2", user_id=1)

    assert complete is True
    assert "f2" not in oauth_google._pending_flows
    tokens = oauth_google.take_completed_tokens("f2", user_id=1)
    assert tokens.access_token == "at-1"
    assert tokens.refresh_token == "rt-1"


def test_poll_device_flow_wrong_user_raises_not_found():
    flow = oauth_google.DeviceFlow(
        flow_id="f3",
        user_id=1,
        device_code="dc-1",
        user_code="ABC-123",
        verification_uri="https://www.google.com/device",
        expires_at=oauth_google.time.monotonic() + 900,
        interval=5,
    )
    oauth_google._pending_flows["f3"] = flow

    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("should not call Google for a foreign flow")

    with pytest.raises(oauth_google.DeviceFlowNotFoundError):
        oauth_google.poll_device_flow(_client_with(handler), "f3", user_id=99)


def test_poll_device_flow_expired_raises():
    flow = oauth_google.DeviceFlow(
        flow_id="f4",
        user_id=1,
        device_code="dc-1",
        user_code="ABC-123",
        verification_uri="https://www.google.com/device",
        expires_at=oauth_google.time.monotonic() - 1,
        interval=5,
    )
    oauth_google._pending_flows["f4"] = flow

    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("should not call Google once already expired")

    with pytest.raises(oauth_google.DeviceFlowExpiredError):
        oauth_google.poll_device_flow(_client_with(handler), "f4", user_id=1)


def test_poll_device_flow_declined_raises_failed():
    flow = oauth_google.DeviceFlow(
        flow_id="f5",
        user_id=1,
        device_code="dc-1",
        user_code="ABC-123",
        verification_uri="https://www.google.com/device",
        expires_at=oauth_google.time.monotonic() + 900,
        interval=5,
    )
    oauth_google._pending_flows["f5"] = flow

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            400, json={"error": "access_denied", "error_description": "User declined"}
        )

    with pytest.raises(oauth_google.DeviceFlowFailedError):
        oauth_google.poll_device_flow(_client_with(handler), "f5", user_id=1)


def test_refresh_access_token_sends_client_secret():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/token")
        assert "client_secret=test-client-secret" in request.content.decode()
        return httpx.Response(
            200,
            json={"access_token": "at-new", "refresh_token": "rt-new", "expires_in": 3600},
        )

    result = oauth_google.refresh_access_token(_client_with(handler), "rt-old")

    assert result.access_token == "at-new"
    assert result.refresh_token == "rt-new"


def test_refresh_access_token_keeps_old_token_if_not_rotated():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"access_token": "at-new", "expires_in": 3600})

    result = oauth_google.refresh_access_token(_client_with(handler), "rt-old")

    assert result.refresh_token == "rt-old"


def test_refresh_access_token_raises_on_http_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={"error": "invalid_grant"})

    with pytest.raises(httpx.HTTPStatusError):
        oauth_google.refresh_access_token(_client_with(handler), "revoked-token")
