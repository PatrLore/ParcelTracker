"""Tests for ParcelServerApiClient against a real (in-process, no live
network) aiohttp server standing in for the backend - exercises the actual
HTTP request/response handling, not just mocked calls."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
from aiohttp import ClientSession, web
from aiohttp.test_utils import TestServer

# api.py has no homeassistant.* imports of its own, but it lives inside the
# parcel_server *package*, whose __init__.py does import homeassistant/
# voluptuous (not installed here). Load it as a standalone module straight
# from its file so importing it doesn't run the package __init__.
_API_PATH = (
    Path(__file__).resolve().parent.parent / "custom_components" / "parcel_server" / "api.py"
)
_spec = importlib.util.spec_from_file_location("parcel_server_api", _API_PATH)
_api = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_api)

ParcelServerApiClient = _api.ParcelServerApiClient
ParcelServerAuthError = _api.ParcelServerAuthError
ParcelServerConnectionError = _api.ParcelServerConnectionError

VALID_EMAIL = "user@example.com"
VALID_PASSWORD = "correct-password"
TOKEN = "fake-access-token"


def _build_app() -> web.Application:
    app = web.Application()
    state = {"orders": [], "next_order_id": 1}
    app["state"] = state

    async def login(request: web.Request) -> web.Response:
        body = await request.json()
        if body.get("email") != VALID_EMAIL or body.get("password") != VALID_PASSWORD:
            return web.json_response({"detail": "invalid credentials"}, status=401)
        return web.json_response({"access_token": TOKEN, "token_type": "bearer"})

    def _require_auth(request: web.Request) -> web.Response | None:
        if request.headers.get("Authorization") != f"Bearer {TOKEN}":
            return web.json_response({"detail": "unauthorized"}, status=401)
        return None

    async def dashboard_summary(request: web.Request) -> web.Response:
        if (unauthorized := _require_auth(request)) is not None:
            return unauthorized
        return web.json_response(
            {
                "in_transit": 2,
                "delivered_today": 1,
                "expected_tomorrow": 0,
                "delayed": 0,
                "new_confirmations": 1,
                "recent_shipments": [],
            }
        )

    async def statistics_summary(request: web.Request) -> web.Response:
        if (unauthorized := _require_auth(request)) is not None:
            return unauthorized
        return web.json_response(
            {
                "parcels_per_month": [],
                "average_delivery_days": 3.5,
                "top_merchant": "Amazon",
                "top_carrier": "DHL",
                "delayed_rate": 0.0,
                "success_rate": 1.0,
                "total_shipments": 5,
            }
        )

    async def list_orders(request: web.Request) -> web.Response:
        if (unauthorized := _require_auth(request)) is not None:
            return unauthorized
        return web.json_response(app["state"]["orders"])

    async def refresh_tracking(request: web.Request) -> web.Response:
        if (unauthorized := _require_auth(request)) is not None:
            return unauthorized
        return web.json_response({"id": int(request.match_info["shipment_id"])})

    async def archive_order(request: web.Request) -> web.Response:
        if (unauthorized := _require_auth(request)) is not None:
            return unauthorized
        body = await request.json()
        return web.json_response(
            {"id": int(request.match_info["order_id"]), "archived": body["archived"]}
        )

    async def send_notification(request: web.Request) -> web.Response:
        if (unauthorized := _require_auth(request)) is not None:
            return unauthorized
        return web.json_response({"dispatched": True, "channel_count": 0}, status=202)

    app.router.add_post("/api/v1/auth/login", login)
    app.router.add_get("/api/v1/dashboard/summary", dashboard_summary)
    app.router.add_get("/api/v1/statistics/summary", statistics_summary)
    app.router.add_get("/api/v1/orders", list_orders)
    app.router.add_post("/api/v1/shipments/{shipment_id}/refresh-tracking", refresh_tracking)
    app.router.add_post("/api/v1/orders/{order_id}/archive", archive_order)
    app.router.add_post("/api/v1/notifications/send", send_notification)
    return app


@pytest.fixture()
async def server():
    app = _build_app()
    test_server = TestServer(app)
    await test_server.start_server()
    yield test_server
    await test_server.close()


@pytest.fixture()
async def client(server: TestServer):
    async with ClientSession() as session:
        yield ParcelServerApiClient(session, str(server.make_url("")), VALID_EMAIL, VALID_PASSWORD)


@pytest.mark.asyncio
async def test_login_success(client: ParcelServerApiClient):
    await client.async_login()
    assert client._access_token == TOKEN


@pytest.mark.asyncio
async def test_login_with_wrong_password_raises_auth_error(server: TestServer):
    async with ClientSession() as session:
        bad_client = ParcelServerApiClient(
            session, str(server.make_url("")), VALID_EMAIL, "wrong-password"
        )
        with pytest.raises(ParcelServerAuthError):
            await bad_client.async_login()


@pytest.mark.asyncio
async def test_get_dashboard_summary_logs_in_automatically(client: ParcelServerApiClient):
    summary = await client.async_get_dashboard_summary()
    assert summary["in_transit"] == 2


@pytest.mark.asyncio
async def test_get_statistics_summary(client: ParcelServerApiClient):
    summary = await client.async_get_statistics_summary()
    assert summary["top_merchant"] == "Amazon"
    assert summary["top_carrier"] == "DHL"


@pytest.mark.asyncio
async def test_refresh_tracking(client: ParcelServerApiClient):
    result = await client.async_refresh_tracking(42)
    assert result["id"] == 42


@pytest.mark.asyncio
async def test_archive_order(client: ParcelServerApiClient):
    result = await client.async_archive_order(17, archived=True)
    assert result == {"id": 17, "archived": True}


@pytest.mark.asyncio
async def test_send_notification(client: ParcelServerApiClient):
    result = await client.async_send_notification("Hi", "Body")
    assert result == {"dispatched": True, "channel_count": 0}


@pytest.mark.asyncio
async def test_expired_token_triggers_one_relogin(client: ParcelServerApiClient):
    await client.async_login()
    client._access_token = "stale-token"  # simulate an expired/invalidated token

    summary = await client.async_get_dashboard_summary()

    assert summary["in_transit"] == 2
    assert client._access_token == TOKEN


@pytest.mark.asyncio
async def test_connection_error_on_unreachable_host():
    async with ClientSession() as session:
        unreachable = ParcelServerApiClient(
            session, "http://127.0.0.1:1", VALID_EMAIL, VALID_PASSWORD
        )
        with pytest.raises(ParcelServerConnectionError):
            await unreachable.async_login()
