"""Tests for concrete TrackingProvider implementations.

Each test injects an ``httpx.Client`` backed by ``httpx.MockTransport`` -
no real network calls are made. Requests are asserted for correctness;
responses are fabricated to match each provider's documented schema (see
each provider module's docstring).
"""

from __future__ import annotations

import httpx
import pytest
from tracking.providers.aftership import AfterShipProvider
from tracking.providers.seventeentrack import SeventeenTrackProvider
from tracking.providers.ship24 import Ship24Provider
from tracking.providers.trackingmore import TrackingMoreProvider


def _client_with(handler, base_url: str, headers: dict[str, str]) -> httpx.Client:
    return httpx.Client(base_url=base_url, headers=headers, transport=httpx.MockTransport(handler))


# --- 17TRACK ---------------------------------------------------------------


def test_seventeentrack_register_sends_correct_request():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["method"] = request.method
        captured["url"] = str(request.url)
        captured["token"] = request.headers.get("17token")
        return httpx.Response(200, json={"code": 0, "data": {"accepted": []}})

    client = _client_with(handler, "https://api.17track.net/track/v2.2", {"17token": "key123"})
    provider = SeventeenTrackProvider(api_key="key123", client=client)

    provider.register("1Z999AA10123456784")

    assert captured["method"] == "POST"
    assert captured["url"].endswith("/register")
    assert captured["token"] == "key123"


def test_seventeentrack_update_parses_events():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "code": 0,
                "data": {
                    "accepted": [
                        {
                            "number": "1Z999AA10123456784",
                            "track": {
                                "z0": [
                                    {
                                        "a": "2026-07-01T10:00:00+00:00",
                                        "z": "Delivered",
                                        "c": "Berlin",
                                    }
                                ]
                            },
                        }
                    ]
                },
            },
        )

    client = _client_with(handler, "https://api.17track.net/track/v2.2", {})
    provider = SeventeenTrackProvider(api_key="key123", client=client)

    events = provider.update("1Z999AA10123456784")

    assert len(events) == 1
    assert events[0].status == "delivered"
    assert events[0].location == "Berlin"


# --- AfterShip ---------------------------------------------------------------


def test_aftership_register_sends_correct_request():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["method"] = request.method
        captured["url"] = str(request.url)
        captured["api_key"] = request.headers.get("aftership-api-key")
        return httpx.Response(200, json={"data": {"tracking": {}}})

    client = _client_with(handler, "https://api.aftership.com/v4", {"aftership-api-key": "key"})
    provider = AfterShipProvider(api_key="key", client=client)

    provider.register("1Z999AA10123456784")

    assert captured["method"] == "POST"
    assert captured["url"].endswith("/trackings")
    assert captured["api_key"] == "key"


def test_aftership_update_parses_events():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "data": {
                    "trackings": [
                        {
                            "slug": "ups",
                            "checkpoints": [
                                {
                                    "tag": "OutForDelivery",
                                    "message": "Out for delivery",
                                    "location": "Munich",
                                    "checkpoint_time": "2026-07-02T08:00:00+00:00",
                                }
                            ],
                        }
                    ]
                }
            },
        )

    client = _client_with(handler, "https://api.aftership.com/v4", {})
    provider = AfterShipProvider(api_key="key", client=client)

    events = provider.update("1Z999AA10123456784")

    assert len(events) == 1
    assert events[0].status == "out_for_delivery"
    assert events[0].location == "Munich"


# --- TrackingMore ---------------------------------------------------------------


def test_trackingmore_register_sends_correct_request():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["method"] = request.method
        captured["url"] = str(request.url)
        captured["api_key"] = request.headers.get("tracking-api-key")
        return httpx.Response(200, json={"data": {}})

    client = _client_with(handler, "https://api.trackingmore.com/v4", {"Tracking-Api-Key": "key"})
    provider = TrackingMoreProvider(api_key="key", client=client)

    provider.register("12345678901234")

    assert captured["method"] == "POST"
    assert captured["url"].endswith("/trackings/create")
    assert captured["api_key"] == "key"


def test_trackingmore_update_parses_events():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "data": [
                    {
                        "origin_info": {
                            "trackinfo": [
                                {
                                    "checkpoint_delivery_status": "delivered",
                                    "tracking_detail": "Package delivered",
                                    "location": "Hamburg",
                                    "checkpoint_date": "2026-07-03T12:00:00+00:00",
                                }
                            ]
                        }
                    }
                ]
            },
        )

    client = _client_with(handler, "https://api.trackingmore.com/v4", {})
    provider = TrackingMoreProvider(api_key="key", client=client)

    events = provider.update("12345678901234")

    assert len(events) == 1
    assert events[0].status == "delivered"
    assert events[0].location == "Hamburg"


# --- Ship24 ---------------------------------------------------------------


def test_ship24_register_caches_tracker_id():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"data": {"tracker": {"trackerId": "tracker-abc"}}})

    client = _client_with(
        handler, "https://api.ship24.com/public/v1", {"Authorization": "Bearer key"}
    )
    provider = Ship24Provider(api_key="key", client=client)

    provider.register("TBA123456789012")

    assert provider._tracker_ids["TBA123456789012"] == "tracker-abc"


def test_ship24_update_registers_first_if_unknown_then_fetches_results():
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url))
        if request.url.path.endswith("/trackers"):
            return httpx.Response(200, json={"data": {"tracker": {"trackerId": "tracker-xyz"}}})
        return httpx.Response(
            200,
            json={
                "data": {
                    "trackings": [
                        {
                            "events": [
                                {
                                    "milestone": "delivered",
                                    "status": "Delivered to recipient",
                                    "location": "Vienna",
                                    "occurrenceDatetime": "2026-07-04T09:00:00+00:00",
                                }
                            ]
                        }
                    ]
                }
            },
        )

    client = _client_with(
        handler, "https://api.ship24.com/public/v1", {"Authorization": "Bearer key"}
    )
    provider = Ship24Provider(api_key="key", client=client)

    events = provider.update("TBA123456789012")

    assert any(call.endswith("/trackers") for call in calls)
    assert any("/results" in call for call in calls)
    assert len(events) == 1
    assert events[0].status == "delivered"
    assert events[0].location == "Vienna"


def test_ship24_remove_without_prior_register_is_noop():
    def handler(request: httpx.Request) -> httpx.Response:
        pytest.fail("should not make a request when tracker is unknown")

    client = _client_with(
        handler, "https://api.ship24.com/public/v1", {"Authorization": "Bearer key"}
    )
    provider = Ship24Provider(api_key="key", client=client)

    provider.remove("unknown-number")
