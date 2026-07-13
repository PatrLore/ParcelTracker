"""17TRACK (https://www.17track.net) tracking provider.

Implements the v2.2 REST API (register / gettrackinfo / deletetrackinfo).
The response field names below (``track.z0[].a``/``z``/``c``) follow
17TRACK's documented event-array shape; adjust ``_events_from_response`` if
17TRACK changes it.
"""

from __future__ import annotations

import httpx

from tracking.provider import TrackingProvider, TrackingProviderEvent
from tracking.providers._status_mapping import infer_status_from_text
from tracking.providers._util import parse_timestamp

_BASE_URL = "https://api.17track.net/track/v2.2"


class SeventeenTrackProvider(TrackingProvider):
    def __init__(self, api_key: str, client: httpx.Client | None = None) -> None:
        self._client = client or httpx.Client(
            base_url=_BASE_URL,
            headers={"17token": api_key, "Content-Type": "application/json"},
            timeout=10.0,
        )

    def register(self, tracking_number: str, carrier_hint: str | None = None) -> None:
        response = self._client.post("/register", json=[{"number": tracking_number}])
        response.raise_for_status()

    def update(self, tracking_number: str) -> list[TrackingProviderEvent]:
        response = self._client.post("/gettrackinfo", json=[{"number": tracking_number}])
        response.raise_for_status()
        return _events_from_response(response.json())

    def remove(self, tracking_number: str) -> None:
        response = self._client.post("/deletetrackinfo", json=[{"number": tracking_number}])
        response.raise_for_status()


def _events_from_response(body: dict) -> list[TrackingProviderEvent]:
    events: list[TrackingProviderEvent] = []
    for item in body.get("data", {}).get("accepted", []):
        for raw_event in item.get("track", {}).get("z0", []):
            description = raw_event.get("z")
            events.append(
                TrackingProviderEvent(
                    status=infer_status_from_text(description),
                    description=description,
                    location=raw_event.get("c"),
                    occurred_at=parse_timestamp(raw_event.get("a")),
                )
            )
    return events
