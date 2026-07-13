"""TrackingMore (https://www.trackingmore.com) tracking provider.

Implements the v4 REST API.
"""

from __future__ import annotations

import httpx

from tracking.provider import TrackingProvider, TrackingProviderEvent
from tracking.providers._util import parse_timestamp

_BASE_URL = "https://api.trackingmore.com/v4"

#: TrackingMore's `checkpoint_delivery_status` enum maps directly onto our
#: own vocabulary; unrecognized values fall back to "in_transit".
_STATUS_MAP = {
    "pending": "label_created",
    "notfound": "label_created",
    "transit": "in_transit",
    "pickup": "out_for_delivery",
    "delivered": "delivered",
    "undelivered": "exception",
    "exception": "exception",
    "expired": "exception",
}


class TrackingMoreProvider(TrackingProvider):
    def __init__(self, api_key: str, client: httpx.Client | None = None) -> None:
        self._client = client or httpx.Client(
            base_url=_BASE_URL,
            headers={"Tracking-Api-Key": api_key, "Content-Type": "application/json"},
            timeout=10.0,
        )

    def register(self, tracking_number: str, carrier_hint: str | None = None) -> None:
        response = self._client.post("/trackings/create", json={"tracking_number": tracking_number})
        response.raise_for_status()

    def update(self, tracking_number: str) -> list[TrackingProviderEvent]:
        response = self._client.get("/trackings/get", params={"tracking_numbers": tracking_number})
        response.raise_for_status()
        return _events_from_response(response.json())

    def remove(self, tracking_number: str) -> None:
        courier_code = self._find_courier_code(tracking_number)
        if courier_code is None:
            return
        response = self._client.delete(f"/trackings/{courier_code}/{tracking_number}")
        response.raise_for_status()

    def _find_courier_code(self, tracking_number: str) -> str | None:
        response = self._client.get("/trackings/get", params={"tracking_numbers": tracking_number})
        response.raise_for_status()
        items = response.json().get("data", [])
        return items[0].get("courier_code") if items else None


def _events_from_response(body: dict) -> list[TrackingProviderEvent]:
    events: list[TrackingProviderEvent] = []
    for item in body.get("data", []):
        for checkpoint in item.get("origin_info", {}).get("trackinfo", []):
            events.append(
                TrackingProviderEvent(
                    status=_STATUS_MAP.get(
                        str(checkpoint.get("checkpoint_delivery_status", "")).lower(), "in_transit"
                    ),
                    description=checkpoint.get("tracking_detail"),
                    location=checkpoint.get("location"),
                    occurred_at=parse_timestamp(checkpoint.get("checkpoint_date")),
                )
            )
    return events
