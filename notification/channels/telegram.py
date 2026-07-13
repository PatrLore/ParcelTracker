"""Telegram channel via the Bot API (https://core.telegram.org/bots/api)."""

from __future__ import annotations

import httpx

from notification.channel import NotificationChannel
from notification.message import NotificationMessage


class TelegramChannel(NotificationChannel):
    def __init__(self, bot_token: str, chat_id: str, client: httpx.Client | None = None) -> None:
        self._chat_id = chat_id
        self._client = client or httpx.Client(
            base_url=f"https://api.telegram.org/bot{bot_token}", timeout=10.0
        )

    def send(self, message: NotificationMessage) -> None:
        response = self._client.post(
            "/sendMessage",
            json={"chat_id": self._chat_id, "text": f"{message.title}\n\n{message.body}"},
        )
        response.raise_for_status()
