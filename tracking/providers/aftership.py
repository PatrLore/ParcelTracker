"""AfterShip (https://www.aftership.com) tracking provider.

Implements the v4 REST API. Uses AfterShip's automatic courier detection
(no ``slug`` required at creation time) and its tracking-number-based
lookup, so no provider-side ID needs to be cached between calls.
"""

from __future__ import annotations

import httpx

from tracking.provider import TrackingProvider, TrackingProviderEvent
from tracking.providers._util import parse_timestamp

_BASE_URL = "https://api.aftership.com/v4"

#: AfterShip's checkpoint "tag" enum maps directly onto our own vocabulary
#: for every value except casing/spelling; unrecognized tags fall back to
#: "in_transit" rather than being dropped.
_TAG_MAP = {
    "pending": "label_created",
    "inforeceived": "label_created",
    "intransit": "in_transit",
    "outfordelivery": "out_for_delivery",
    "attemptfail": "exception",
    "delivered": "delivered",
    "exception": "exception",
    "expired": "exception",
}


class AfterShipProvider(TrackingProvider):
    def __init__(self, api_key: str, client: httpx.Client | None = None) -> None:
        self._client = client or httpx.Client(
            base_url=_BASE_URL,
            headers={"aftership-api-key": api_key, "Content-Type": "application/json"},
            timeout=10.0,
        )

    def register(self, tracking_number: str, carrier_hint: str | None = None) -> None:
        response = self._client.post(
            "/trackings", json={"tracking": {"tracking_number": tracking_number}}
        )
        response.raise_for_status()

    def update(self, tracking_number: str) -> list[TrackingProviderEvent]:
        response = self._client.get("/trackings", params={"tracking_numbers": tracking_number})
        response.raise_for_status()
        return _events_from_response(response.json())

    def remove(self, tracking_number: str) -> None:
        slug = self._find_slug(tracking_number)
        if slug is None:
            return
        response = self._client.delete(f"/trackings/{slug}/{tracking_number}")
        response.raise_for_status()

    def _find_slug(self, tracking_number: str) -> str | None:
        response = self._client.get("/trackings", params={"tracking_numbers": tracking_number})
        response.raise_for_status()
        trackings = response.json().get("data", {}).get("trackings", [])
        return trackings[0]["slug"] if trackings else None


def _events_from_response(body: dict) -> list[TrackingProviderEvent]:
    events: list[TrackingProviderEvent] = []
    for tracking in body.get("data", {}).get("trackings", []):
        for checkpoint in tracking.get("checkpoints", []):
            events.append(
                TrackingProviderEvent(
                    status=_TAG_MAP.get(str(checkpoint.get("tag", "")).lower(), "in_transit"),
                    description=checkpoint.get("message"),
                    location=checkpoint.get("location"),
                    occurred_at=parse_timestamp(checkpoint.get("checkpoint_time")),
                )
            )
    return events
