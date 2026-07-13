"""Fans a notification out to every configured channel, independently."""

from __future__ import annotations

import logging

from notification.channel import NotificationChannel
from notification.message import NotificationMessage

logger = logging.getLogger(__name__)


class NotificationDispatcher:
    def __init__(self, channels: list[NotificationChannel]) -> None:
        self._channels = channels

    @property
    def channels(self) -> tuple[NotificationChannel, ...]:
        return tuple(self._channels)

    def dispatch(self, message: NotificationMessage) -> None:
        """Send to every channel. One channel failing doesn't stop the rest -
        channels raise arbitrary, channel-specific exceptions (HTTP errors,
        SMTP errors, ...), so this boundary deliberately catches broadly."""
        for channel in self._channels:
            try:
                channel.send(message)
            except Exception:
                logger.exception("Notification channel %s failed to send", type(channel).__name__)
