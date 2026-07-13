"""Pluggable notification channels: Telegram, Signal, Discord, Email, and
generic webhooks. (MQTT / Home Assistant Discovery is the separate `mqtt`
package - it publishes sensor state rather than one-off messages.)
"""

from notification.channel import NotificationChannel
from notification.dispatcher import NotificationDispatcher
from notification.message import NotificationMessage

__all__ = ["NotificationChannel", "NotificationDispatcher", "NotificationMessage"]
