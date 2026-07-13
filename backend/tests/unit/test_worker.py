"""Unit tests for the import worker's due-for-sync scheduling logic."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.models.mail_account import MailAccount
from app.worker import _due_for_sync


def _account(last_synced_at=None, poll_interval_seconds=300) -> MailAccount:
    return MailAccount(
        email_address="x@example.com",
        imap_host="imap.example.com",
        imap_username="x@example.com",
        encrypted_password="irrelevant",
        poll_interval_seconds=poll_interval_seconds,
        last_synced_at=last_synced_at,
    )


def test_never_synced_account_is_due():
    assert _due_for_sync(_account(last_synced_at=None), datetime.now(UTC)) is True


def test_recently_synced_account_is_not_due():
    now = datetime.now(UTC)
    account = _account(last_synced_at=now - timedelta(seconds=10), poll_interval_seconds=300)
    assert _due_for_sync(account, now) is False


def test_account_past_its_poll_interval_is_due():
    now = datetime.now(UTC)
    account = _account(last_synced_at=now - timedelta(seconds=301), poll_interval_seconds=300)
    assert _due_for_sync(account, now) is True
