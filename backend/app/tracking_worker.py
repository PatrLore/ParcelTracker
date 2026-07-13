"""Standalone tracking-refresh worker.

Two independent periodic jobs, each on its own configured interval:

- Tracking sync (Phase 3): polls the configured TrackingProvider for every
  non-terminal shipment. If no provider is configured
  (``tracking_provider.name: "none"``), this job idles and logs once - the
  API/dashboard keep working from email-derived data alone.
- MQTT publish (Phase 4): pushes aggregate parcel counts to MQTT as Home
  Assistant Discovery sensors. Idles if ``mqtt.enabled`` is false.

Runs as a separate process/container from the API server and the mail
import worker, so a slow or rate-limited tracking provider (or MQTT broker)
never blocks either of those.
"""

from __future__ import annotations

import time
from datetime import UTC, datetime

import httpx

from app.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.database import SessionLocal
from app.services.mqtt_publish_service import MqttPublishService
from app.services.mqtt_publisher_factory import get_configured_mqtt_publisher
from app.services.notification_dispatch_factory import get_configured_notification_dispatcher
from app.services.tracking_provider_factory import get_configured_tracking_provider
from app.services.tracking_sync_service import TrackingSyncService

logger = get_logger(__name__)

TICK_SECONDS = 30


def _due(last_run: datetime | None, interval_seconds: int, now: datetime) -> bool:
    if last_run is None:
        return True
    return (now - last_run).total_seconds() >= interval_seconds


def run_tracking_sync() -> None:
    provider = get_configured_tracking_provider()
    if provider is None:
        logger.info("No tracking provider configured (tracking_provider.name is 'none') - idling")
        return

    dispatcher = get_configured_notification_dispatcher()
    with SessionLocal() as db:
        try:
            synced = TrackingSyncService(db, provider, dispatcher).sync_due_shipments()
            logger.info("Refreshed tracking for %d shipment(s)", synced)
        except httpx.HTTPError:
            logger.exception("Tracking provider request failed")


def run_mqtt_publish() -> None:
    publisher = get_configured_mqtt_publisher()
    if publisher is None:
        return

    with SessionLocal() as db:
        try:
            MqttPublishService(db, publisher).publish()
            logger.info("Published parcel sensors to MQTT")
        except OSError:
            logger.exception("MQTT publish failed")


def main() -> None:
    configure_logging()
    logger.info("Starting Parcel Server tracking worker (tick: %ss)", TICK_SECONDS)

    last_tracking_sync: datetime | None = None
    last_mqtt_publish: datetime | None = None

    while True:
        now = datetime.now(UTC)
        settings = get_settings()

        if _due(last_tracking_sync, settings.tracking_provider.poll_interval_seconds, now):
            run_tracking_sync()
            last_tracking_sync = now

        if _due(last_mqtt_publish, settings.mqtt.publish_interval_seconds, now):
            run_mqtt_publish()
            last_mqtt_publish = now

        time.sleep(TICK_SECONDS)


if __name__ == "__main__":
    main()
