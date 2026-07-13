"""Signal channel via signal-cli-rest-api
(https://github.com/bbernhard/signal-cli-rest-api).

Signal has no official bot/webhook API; self-hosting that REST wrapper
around signal-cli is the standard way to send Signal messages
programmatically. ``base_url`` must point at that sidecar's HTTP API, not
at any Signal server directly.
"""

from __future__ import annotations

import httpx

from notification.channel import NotificationChannel
from notification.message import NotificationMessage


class SignalChannel(NotificationChannel):
    def __init__(
        self,
        base_url: str,
        sender_number: str,
        recipient_number: str,
        client: httpx.Client | None = None,
    ) -> None:
        self._sender_number = sender_number
        self._recipient_number = recipient_number
        self._client = client or httpx.Client(base_url=base_url, timeout=10.0)

    def send(self, message: NotificationMessage) -> None:
        response = self._client.post(
            "/v2/send",
            json={
                "message": f"{message.title}\n\n{message.body}",
                "number": self._sender_number,
                "recipients": [self._recipient_number],
            },
        )
        response.raise_for_status()
