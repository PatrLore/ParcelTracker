"""Tests for NotificationDispatcher's fan-out and per-channel isolation."""

from __future__ import annotations

from notification.channel import NotificationChannel
from notification.dispatcher import NotificationDispatcher
from notification.message import NotificationMessage


class RecordingChannel(NotificationChannel):
    def __init__(self) -> None:
        self.sent: list[NotificationMessage] = []

    def send(self, message: NotificationMessage) -> None:
        self.sent.append(message)


class FailingChannel(NotificationChannel):
    def send(self, message: NotificationMessage) -> None:
        raise RuntimeError("channel unreachable")


def test_dispatch_sends_to_every_channel():
    a, b = RecordingChannel(), RecordingChannel()
    dispatcher = NotificationDispatcher([a, b])
    message = NotificationMessage(event="x", title="Title", body="Body")

    dispatcher.dispatch(message)

    assert a.sent == [message]
    assert b.sent == [message]


def test_one_failing_channel_does_not_block_the_others():
    recording = RecordingChannel()
    dispatcher = NotificationDispatcher([FailingChannel(), recording])
    message = NotificationMessage(event="x", title="Title", body="Body")

    dispatcher.dispatch(message)  # must not raise

    assert recording.sent == [message]
