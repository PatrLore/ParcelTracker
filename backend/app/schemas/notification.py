"""Manual notification-send schema (used by the trigger-a-notification
endpoint, e.g. from the Home Assistant integration's ``send_notification``
service)."""

from __future__ import annotations

from pydantic import BaseModel


class NotificationSendRequest(BaseModel):
    title: str
    body: str
    event: str = "manual"


class NotificationSendResult(BaseModel):
    dispatched: bool
    channel_count: int
