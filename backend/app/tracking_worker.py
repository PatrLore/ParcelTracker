"""Standalone tracking-refresh worker: polls the configured TrackingProvider
for every non-terminal shipment on a fixed interval (Phase 3).

Runs as a separate process/container from the API server and the mail
import worker, so a slow or rate-limited tracking provider never blocks
either of those. If no provider is configured
(``tracking_provider.name: "none"``), the loop idles and logs once - the
API/dashboard keep working from email-derived data alone.
"""

from __future__ import annotations

import time

import httpx

from app.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.database import SessionLocal
from app.services.tracking_provider_factory import get_configured_tracking_provider
from app.services.tracking_sync_service import TrackingSyncService

logger = get_logger(__name__)


def run_once() -> None:
    """Sync every non-terminal shipment a single time, if a provider is configured."""
    provider = get_configured_tracking_provider()
    if provider is None:
        logger.info("No tracking provider configured (tracking_provider.name is 'none') - idling")
        return

    with SessionLocal() as db:
        try:
            synced = TrackingSyncService(db, provider).sync_due_shipments()
            logger.info("Refreshed tracking for %d shipment(s)", synced)
        except httpx.HTTPError:
            logger.exception("Tracking provider request failed")


def main() -> None:
    configure_logging()
    poll_interval = get_settings().tracking_provider.poll_interval_seconds
    logger.info("Starting Parcel Server tracking worker (poll interval: %ss)", poll_interval)
    while True:
        run_once()
        time.sleep(poll_interval)


if __name__ == "__main__":
    main()
