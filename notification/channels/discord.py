"""Discord channel: posts to an incoming webhook URL."""

from __future__ import annotations

import httpx

from notification.channel import NotificationChannel
from notification.message import NotificationMessage


class DiscordChannel(NotificationChannel):
    def __init__(self, webhook_url: str, client: httpx.Client | None = None) -> None:
        self._webhook_url = webhook_url
        self._client = client or httpx.Client(timeout=10.0)

    def send(self, message: NotificationMessage) -> None:
        response = self._client.post(
            self._webhook_url, json={"content": f"**{message.title}**\n{message.body}"}
        )
        response.raise_for_status()
