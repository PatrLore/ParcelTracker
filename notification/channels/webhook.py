"""Generic outgoing webhook channel: POSTs a JSON payload to a configured URL."""

from __future__ import annotations

import httpx

from notification.channel import NotificationChannel
from notification.message import NotificationMessage


class WebhookChannel(NotificationChannel):
    def __init__(self, url: str, client: httpx.Client | None = None) -> None:
        self._url = url
        self._client = client or httpx.Client(timeout=10.0)

    def send(self, message: NotificationMessage) -> None:
        response = self._client.post(
            self._url,
            json={
                "event": message.event,
                "title": message.title,
                "body": message.body,
                "metadata": message.metadata,
            },
        )
        response.raise_for_status()
