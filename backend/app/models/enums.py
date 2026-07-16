"""Shared enumerations used across ORM models and API schemas."""

from __future__ import annotations

import enum


class OrderStatus(enum.StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    RETURNED = "returned"


class ShipmentStatus(enum.StrEnum):
    UNKNOWN = "unknown"
    LABEL_CREATED = "label_created"
    IN_TRANSIT = "in_transit"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    DELAYED = "delayed"
    EXCEPTION = "exception"
    RETURNED = "returned"


class MailAccountAuthType(enum.StrEnum):
    """How a :class:`~app.models.mail_account.MailAccount` authenticates to
    its IMAP server. ``OAUTH_MICROSOFT`` exists because Microsoft retired
    plain-password Basic Authentication for Outlook.com/Hotmail/Live
    accounts; ``OAUTH_GOOGLE`` is an alternative to a Gmail app password -
    see ``docs/mailboxes.md``."""

    PASSWORD = "password"
    OAUTH_MICROSOFT = "oauth_microsoft"
    OAUTH_GOOGLE = "oauth_google"
