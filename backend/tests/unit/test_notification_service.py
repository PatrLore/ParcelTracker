"""Unit tests for the manual notification-send service. Uses a recording
NotificationChannel - no real HTTP/SMTP/etc. calls, matching the convention
in test_notification_dispatch_wiring.py."""

from __future__ import annotations

from notification import NotificationChannel, NotificationDispatcher, NotificationMessage

from app.schemas.notification import NotificationSendRequest
from app.services.notification_service import NotificationService


class RecordingChannel(NotificationChannel):
    def __init__(self) -> None:
        self.sent: list[NotificationMessage] = []

    def send(self, message: NotificationMessage) -> None:
        self.sent.append(message)


def test_send_dispatches_message_and_reports_channel_count():
    channel = RecordingChannel()
    service = NotificationService(NotificationDispatcher([channel]))

    result = service.send(NotificationSendRequest(title="Hi", body="Body text", event="test"))

    assert result.dispatched is True
    assert result.channel_count == 1
    assert channel.sent[0].title == "Hi"
    assert channel.sent[0].event == "test"


def test_send_with_no_configured_channels_still_reports_dispatched():
    service = NotificationService(NotificationDispatcher([]))

    result = service.send(NotificationSendRequest(title="Hi", body="Body text"))

    assert result.dispatched is True
    assert result.channel_count == 0
