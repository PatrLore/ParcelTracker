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
