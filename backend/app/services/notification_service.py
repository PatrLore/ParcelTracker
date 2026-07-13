"""Business logic for manually-triggered notifications (as opposed to the
ones the tracking sync/email ingestion services fire automatically)."""

from __future__ import annotations

from notification import NotificationDispatcher, NotificationMessage

from app.schemas.notification import NotificationSendRequest, NotificationSendResult


class NotificationService:
    def __init__(self, dispatcher: NotificationDispatcher) -> None:
        self.dispatcher = dispatcher

    def send(self, data: NotificationSendRequest) -> NotificationSendResult:
        message = NotificationMessage(event=data.event, title=data.title, body=data.body)
        self.dispatcher.dispatch(message)
        return NotificationSendResult(dispatched=True, channel_count=len(self.dispatcher.channels))
