"""Builds a NotificationDispatcher from the channels enabled in ``config.yaml``.

The only backend module that imports concrete `notification.channels.*`
classes - the rest of the backend only ever sees
:class:`notification.dispatcher.NotificationDispatcher`.
"""

from __future__ import annotations

from notification import NotificationChannel, NotificationDispatcher
from notification.channels.discord import DiscordChannel
from notification.channels.email_smtp import EmailChannel
from notification.channels.signal import SignalChannel
from notification.channels.telegram import TelegramChannel
from notification.channels.webhook import WebhookChannel

from app.config import get_settings


def get_configured_notification_dispatcher() -> NotificationDispatcher:
    """Returns a dispatcher wrapping every enabled channel (possibly none)."""
    settings = get_settings().notification
    channels: list[NotificationChannel] = []

    if settings.webhook.enabled:
        channels.append(WebhookChannel(settings.webhook.url))
    if settings.discord.enabled:
        channels.append(DiscordChannel(settings.discord.webhook_url))
    if settings.telegram.enabled:
        channels.append(TelegramChannel(settings.telegram.bot_token, settings.telegram.chat_id))
    if settings.signal.enabled:
        channels.append(
            SignalChannel(
                settings.signal.base_url,
                settings.signal.sender_number,
                settings.signal.recipient_number,
            )
        )
    if settings.email.enabled:
        channels.append(
            EmailChannel(
                smtp_host=settings.email.smtp_host,
                smtp_port=settings.email.smtp_port,
                username=settings.email.username,
                password=settings.email.password,
                from_address=settings.email.from_address,
                to_address=settings.email.to_address,
                use_tls=settings.email.use_tls,
            )
        )

    return NotificationDispatcher(channels)
