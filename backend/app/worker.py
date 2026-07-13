"""Standalone import worker: polls every active mail account for new mail.

Runs as a separate process/container from the API server (see the `worker`
service in docker-compose.yml) so a slow or unreachable mailbox never blocks
API requests. Each account is synced no more often than its own
``poll_interval_seconds``. IDLE-based push notification
(``ImapMailbox.idle_check``) is available in ``importer`` but not yet wired
into this loop - a future phase can add a per-account IDLE runner for
accounts with ``use_idle=True`` without changing the polling path here.
"""

from __future__ import annotations

import time
from datetime import UTC, datetime

from app.core.logging import configure_logging, get_logger
from app.database import SessionLocal
from app.models.mail_account import MailAccount
from app.repositories.mail_account_repository import MailAccountRepository
from app.services.email_ingestion_service import EmailIngestionService
from app.services.notification_dispatch_factory import get_configured_notification_dispatcher

logger = get_logger(__name__)

TICK_SECONDS = 30


def _due_for_sync(account: MailAccount, now: datetime) -> bool:
    if account.last_synced_at is None:
        return True
    elapsed = (now - account.last_synced_at).total_seconds()
    return elapsed >= account.poll_interval_seconds


def run_once() -> None:
    """Sync every active, due mail account a single time."""
    dispatcher = get_configured_notification_dispatcher()

    with SessionLocal() as db:
        accounts = MailAccountRepository(db).list_active()
        now = datetime.now(UTC)

        for account in accounts:
            if not _due_for_sync(account, now):
                continue
            try:
                result = EmailIngestionService(db, dispatcher=dispatcher).sync_account(account)
                logger.info(
                    "Synced %s: %d new email(s), %d matched order(s), %d new shipment(s)",
                    account.email_address,
                    result.fetched_emails,
                    result.matched_orders,
                    result.created_shipments,
                )
            except Exception:
                logger.exception("Failed to sync mail account %s", account.email_address)


def main() -> None:
    configure_logging()
    logger.info("Starting Parcel Server import worker (tick: %ss)", TICK_SECONDS)
    while True:
        run_once()
        time.sleep(TICK_SECONDS)


if __name__ == "__main__":
    main()
