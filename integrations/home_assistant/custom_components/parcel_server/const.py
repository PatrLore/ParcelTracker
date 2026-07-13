"""Constants for the Parcel Server integration."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "parcel_server"

CONF_BASE_URL = "base_url"
CONF_VERIFY_SSL = "verify_ssl"

DEFAULT_SCAN_INTERVAL = timedelta(seconds=60)

ATTR_MERCHANT = "merchant"
ATTR_CARRIER = "carrier"
ATTR_TRACKING_NUMBER = "tracking_number"
ATTR_ORDER_ID = "order_id"
ATTR_SHIPMENT_ID = "shipment_id"

SERVICE_REFRESH_TRACKING = "refresh_tracking"
SERVICE_ARCHIVE_PARCEL = "archive_parcel"
SERVICE_SEND_NOTIFICATION = "send_notification"

ATTR_ARCHIVED = "archived"
ATTR_TITLE = "title"
ATTR_MESSAGE = "message"
ATTR_EVENT = "event"
