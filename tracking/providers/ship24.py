"""Ship24 (https://www.ship24.com) tracking provider.

Implements the public v1 REST API. Ship24 assigns an opaque ``trackerId``
per registration; this provider caches the ``tracking_number -> trackerId``
mapping in memory so ``update()``/``remove()`` don't need to re-derive it.
That cache does not survive a process restart - a fresh worker process
re-registers on first use for any shipment it hasn't seen yet (harmless:
Ship24 treats re-registering an existing tracking number as a no-op).
"""

from __future__ import annotations

import httpx

from tracking.provider import TrackingProvider, TrackingProviderEvent
from tracking.providers._util import parse_timestamp

_BASE_URL = "https://api.ship24.com/public/v1"

#: Ship24's `milestone` enum maps directly onto our own vocabulary;
#: unrecognized values fall back to "in_transit".
_MILESTONE_MAP = {
    "info_received": "label_created",
    "in_transit": "in_transit",
    "out_for_delivery": "out_for_delivery",
    "failed_attempt": "exception",
    "delivered": "delivered",
    "exception": "exception",
    "expired": "exception",
}


class Ship24Provider(TrackingProvider):
    def __init__(self, api_key: str, client: httpx.Client | None = None) -> None:
        self._client = client or httpx.Client(
            base_url=_BASE_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            timeout=10.0,
        )
        self._tracker_ids: dict[str, str] = {}

    def register(self, tracking_number: str, carrier_hint: str | None = None) -> None:
        response = self._client.post("/trackers", json={"trackingNumber": tracking_number})
        response.raise_for_status()
        tracker_id = response.json().get("data", {}).get("tracker", {}).get("trackerId")
        if tracker_id:
            self._tracker_ids[tracking_number] = tracker_id

    def update(self, tracking_number: str) -> list[TrackingProviderEvent]:
        tracker_id = self._tracker_ids.get(tracking_number)
        if tracker_id is None:
            self.register(tracking_number)
            tracker_id = self._tracker_ids.get(tracking_number)
        if tracker_id is None:
            return []

        response = self._client.get(f"/trackers/{tracker_id}/results")
        response.raise_for_status()
        return _events_from_response(response.json())

    def remove(self, tracking_number: str) -> None:
        tracker_id = self._tracker_ids.pop(tracking_number, None)
        if tracker_id is None:
            return
        response = self._client.delete(f"/trackers/{tracker_id}")
        response.raise_for_status()


def _events_from_response(body: dict) -> list[TrackingProviderEvent]:
    events: list[TrackingProviderEvent] = []
    for tracking in body.get("data", {}).get("trackings", []):
        for event in tracking.get("events", []):
            milestone = str(event.get("milestone", "")).lower()
            events.append(
                TrackingProviderEvent(
                    status=_MILESTONE_MAP.get(milestone, "in_transit"),
                    description=event.get("status"),
                    location=event.get("location"),
                    occurred_at=parse_timestamp(event.get("occurrenceDatetime")),
                )
            )
    return events
