"""Unit tests for EmailIngestionService: fetch -> parse -> persist.

Uses a fake, in-memory mailbox (no real IMAP connection) so these tests are
fast and hermetic - only the backend <-> importer integration is exercised.
"""

from __future__ import annotations

from contextlib import contextmanager
from datetime import UTC, datetime

import httpx
import pytest
from importer.emails import RawEmail

from app.models.enums import OrderStatus, ShipmentStatus
from app.models.order import Order
from app.schemas.mail_account import MailAccountCreate
from app.schemas.user import UserCreate
from app.services.email_ingestion_service import MAX_EMAILS_PER_SYNC, EmailIngestionService
from app.services.mail_account_service import MailAccountService
from app.services.user_service import UserService


class FakeMailbox:
    """Duck-types :class:`importer.imap_client.ImapMailbox` for tests."""

    def __init__(self, config, emails: list[RawEmail]) -> None:
        self.config = config
        self._emails = emails

    @contextmanager
    def session(self):
        yield self

    def fetch_since(self, since_uid: int, limit: int | None = None) -> list[RawEmail]:
        matching = sorted(
            (email for email in self._emails if email.uid > since_uid), key=lambda email: email.uid
        )
        return matching[:limit] if limit is not None else matching


def _fake_factory(emails: list[RawEmail]):
    return lambda config: FakeMailbox(config, emails)


@pytest.fixture()
def user(db_session):
    return UserService(db_session).create_user(
        UserCreate(email="ingestion-owner@example.com", password="password123")
    )


@pytest.fixture()
def mail_account(db_session, user):
    return MailAccountService(db_session).create_account(
        MailAccountCreate(
            email_address="owner@gmail.com",
            imap_host="imap.gmail.com",
            imap_username="owner@gmail.com",
            password="app-password",
        ),
        user.id,
    )


def _amazon_email(uid: int) -> RawEmail:
    return RawEmail(
        uid=uid,
        message_id=f"<amazon-{uid}@example.com>",
        subject="Ihre Bestellung wurde versandt",
        sender="versand@amazon.de",
        received_at=datetime(2026, 7, 1, tzinfo=UTC),
        text_body=(
            "Bestellnummer: 302-1234567-1234567\n"
            "Gesamtbetrag: 29,99 EUR\n"
            "Ihre Sendungsverfolgungsnummer lautet: 1Z999AA10123456784"
        ),
    )


def test_sync_creates_email_order_and_shipment(db_session, mail_account):
    service = EmailIngestionService(db_session, mailbox_factory=_fake_factory([_amazon_email(1)]))

    result = service.sync_account(mail_account)

    assert result.fetched_emails == 1
    assert result.matched_orders == 1
    assert result.created_shipments == 1

    order = db_session.query(Order).one()
    assert order.merchant == "Amazon"
    assert order.order_number == "302-1234567-1234567"
    assert order.status == OrderStatus.SHIPPED

    shipment = order.shipments[0]
    assert shipment.tracking_number == "1Z999AA10123456784"
    assert shipment.tracking_status == ShipmentStatus.LABEL_CREATED
    assert shipment.carrier.name == "UPS"

    assert mail_account.last_seen_uid == 1
    assert mail_account.last_synced_at is not None


def test_sync_refreshes_access_token_for_oauth_microsoft_account(db_session, user):
    account = MailAccountService(db_session).create_oauth_microsoft_account(
        user_id=user.id,
        email_address="owner@hotmail.com",
        refresh_token="rt-1",
        folder="INBOX",
        use_idle=False,
        poll_interval_seconds=300,
    )
    seen_configs = []

    def factory(config):
        seen_configs.append(config)
        return FakeMailbox(config, [_amazon_email(1)])

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, json={"access_token": "at-1", "refresh_token": "rt-2", "expires_in": 3600}
        )

    service = EmailIngestionService(
        db_session,
        mailbox_factory=factory,
        http_client_factory=lambda: httpx.Client(transport=httpx.MockTransport(handler)),
    )

    result = service.sync_account(account)

    assert result.fetched_emails == 1
    assert seen_configs[0].access_token == "at-1"
    assert seen_configs[0].password is None
    assert account.encrypted_oauth_refresh_token != "rt-1"


def test_sync_is_idempotent_across_repeated_fetches(db_session, mail_account):
    emails = [_amazon_email(1)]
    service = EmailIngestionService(db_session, mailbox_factory=_fake_factory(emails))

    service.sync_account(mail_account)
    # Same email fetched again (e.g. a mailbox that doesn't advance UIDs cleanly).
    mail_account.last_seen_uid = 0
    second_result = service.sync_account(mail_account)

    assert second_result.fetched_emails == 1
    assert second_result.matched_orders == 0  # message_id already seen -> skipped


def test_sync_caps_fetch_and_reports_truncated(db_session, mail_account):
    emails = [_amazon_email(uid) for uid in range(1, MAX_EMAILS_PER_SYNC + 51)]
    service = EmailIngestionService(db_session, mailbox_factory=_fake_factory(emails))

    result = service.sync_account(mail_account)

    assert result.fetched_emails == MAX_EMAILS_PER_SYNC
    assert result.truncated is True
    # Only the oldest-first batch was processed - UID advances to the batch's end, not beyond.
    assert mail_account.last_seen_uid == MAX_EMAILS_PER_SYNC

    second_result = service.sync_account(mail_account)

    assert second_result.fetched_emails == 50
    assert second_result.truncated is False
    assert mail_account.last_seen_uid == MAX_EMAILS_PER_SYNC + 50


def test_sync_persists_unmatched_email_without_order(db_session, mail_account):
    email = RawEmail(
        uid=1,
        message_id="<unknown@example.com>",
        subject="Hello",
        sender="someone@unknown-shop.example",
        received_at=datetime(2026, 7, 1, tzinfo=UTC),
        text_body="Nothing shipping-related here.",
    )
    service = EmailIngestionService(db_session, mailbox_factory=_fake_factory([email]))

    result = service.sync_account(mail_account)

    assert result.fetched_emails == 1
    assert result.matched_orders == 0
    assert result.created_shipments == 0
