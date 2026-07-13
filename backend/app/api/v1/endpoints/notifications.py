"""Manual notification trigger - fans a one-off message out to every
configured channel (webhook/Discord/Telegram/Email/Signal). Used by
external callers such as the Home Assistant integration's
``send_notification`` service."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.api.deps import get_current_user
from app.schemas.notification import NotificationSendRequest, NotificationSendResult
from app.services.notification_dispatch_factory import get_configured_notification_dispatcher
from app.services.notification_service import NotificationService

router = APIRouter(
    prefix="/notifications", tags=["notifications"], dependencies=[Depends(get_current_user)]
)


@router.post("/send", response_model=NotificationSendResult, status_code=status.HTTP_202_ACCEPTED)
def send_notification(payload: NotificationSendRequest) -> NotificationSendResult:
    dispatcher = get_configured_notification_dispatcher()
    return NotificationService(dispatcher).send(payload)
