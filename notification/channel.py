"""The notification-channel plugin interface.

Every channel (``notification/channels/*.py``) implements
:class:`NotificationChannel`. Unlike the email importer's merchant parsers,
channels are not auto-discovered: each needs distinct credentials (a
webhook URL, a bot token, SMTP settings, ...), so which channels are active
is an explicit list built from configuration, not something to detect from
the message itself.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from notification.message import NotificationMessage


class NotificationChannel(ABC):
    """A destination a :class:`NotificationMessage` can be delivered to."""

    @abstractmethod
    def send(self, message: NotificationMessage) -> None:
        """Deliver the message. Raises on failure - callers decide whether
        one channel's failure should stop delivery to the others."""
