"""Tests that EmailIngestionService and TrackingSyncService correctly fire
notifications on the events the spec calls for: new confirmations and
delivered/delayed shipments. Uses a recording NotificationChannel - no real
HTTP/SMTP/etc. calls."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import UTC, datetime

import pytest
from importer.emails import RawEmail
from notification import NotificationChannel, NotificationDispatcher, NotificationMessage
from tracking.provider import TrackingProvider, TrackingProviderEvent

from app.models.enums import OrderStatus
from app.schemas.order import OrderCreate
from app.schemas.shipment import ShipmentCreate
from app.schemas.user import UserCreate
from app.services.email_ingestion_service import EmailIngestionService
from app.services.order_service import OrderService
from app.services.shipment_service import ShipmentService
from app.services.tracking_sync_service import TrackingSyncService
from app.services.user_service import UserService


class RecordingChannel(NotificationChannel):
    def __init__(self) -> None:
        self.sent: list[NotificationMessage] = []

    def send(self, message: NotificationMessage) -> None:
        self.sent.append(message)


@pytest.fixture()
def user(db_session):
    return UserService(db_session).create_user(
        UserCreate(email="notify-owner@example.com", password="password123")
    )


def test_new_confirmation_triggers_notification(db_session, user):
    class FakeMailbox:
        def __init__(self, config) -> None:
            pass

        @contextmanager
        def session(self):
            yield self

        def fetch_since(self, since_uid: int) -> list[RawEmail]:
            return [
                RawEmail(
                    uid=1,
                    message_id="<amazon-1@example.com>",
                    subject="Ihre Bestellung wurde versandt",
                    sender="versand@amazon.de",
                    received_at=datetime(2026, 7, 1, tzinfo=UTC),
                    text_body="Bestellnummer: 302-1234567-1234567\nTracking: 1Z999AA10123456784",
                )
            ]

    from app.schemas.mail_account import MailAccountCreate
    from app.services.mail_account_service import MailAccountService

    account = MailAccountService(db_session).create_account(
        MailAccountCreate(
            email_address="owner@gmail.com",
            imap_host="imap.gmail.com",
            imap_username="owner@gmail.com",
            password="app-password",
        ),
        user.id,
    )
    channel = RecordingChannel()
    dispatcher = NotificationDispatcher([channel])
    service = EmailIngestionService(db_session, mailbox_factory=FakeMailbox, dispatcher=dispatcher)

    service.sync_account(account)

    assert len(channel.sent) == 1
    assert channel.sent[0].event == "new_confirmation"
    assert channel.sent[0].metadata["merchant"] == "Amazon"


def test_reused_order_does_not_re_notify(db_session, user):
    """Two emails for the same order number should only notify once - on
    the first, order-creating email."""

    class FakeMailbox:
        def __init__(self, config) -> None:
            pass

        @contextmanager
        def session(self):
            yield self

        def fetch_since(self, since_uid: int) -> list[RawEmail]:
            return [
                RawEmail(
                    uid=since_uid + 1,
                    message_id=f"<amazon-{since_uid + 1}@example.com>",
                    subject="Ihre Bestellung wurde versandt",
                    sender="versand@amazon.de",
                    received_at=datetime(2026, 7, 1, tzinfo=UTC),
                    text_body="Bestellnummer: 302-1234567-1234567\nTracking: 1Z999AA10123456784",
                )
            ]

    from app.schemas.mail_account import MailAccountCreate
    from app.services.mail_account_service import MailAccountService

    account = MailAccountService(db_session).create_account(
        MailAccountCreate(
            email_address="owner@gmail.com",
            imap_host="imap.gmail.com",
            imap_username="owner@gmail.com",
            password="app-password",
        ),
        user.id,
    )
    channel = RecordingChannel()
    dispatcher = NotificationDispatcher([channel])
    service = EmailIngestionService(db_session, mailbox_factory=FakeMailbox, dispatcher=dispatcher)

    service.sync_account(account)
    service.sync_account(account)

    assert len(channel.sent) == 1


class _FakeTrackingProvider(TrackingProvider):
    def __init__(self, events: list[TrackingProviderEvent]) -> None:
        self._events = events

    def register(self, tracking_number: str, carrier_hint: str | None = None) -> None:
        pass

    def update(self, tracking_number: str) -> list[TrackingProviderEvent]:
        return self._events

    def remove(self, tracking_number: str) -> None:
        pass


@pytest.fixture()
def shipment(db_session, user):
    order = OrderService(db_session).create_order(
        OrderCreate(merchant="Amazon", status=OrderStatus.SHIPPED), user.id
    )
    return ShipmentService(db_session).create_shipment(
        ShipmentCreate(tracking_number="1Z999AA10123456784", order_id=order.id)
    )


def test_delivered_shipment_triggers_notification(db_session, shipment):
    channel = RecordingChannel()
    dispatcher = NotificationDispatcher([channel])
    provider = _FakeTrackingProvider(
        events=[
            TrackingProviderEvent(
                status="delivered",
                description="Delivered",
                location="Berlin",
                occurred_at=datetime(2026, 7, 2, tzinfo=UTC),
            )
        ]
    )

    TrackingSyncService(db_session, provider, dispatcher).sync_shipment(shipment)

    assert len(channel.sent) == 1
    assert channel.sent[0].event == "shipment_delivered"


def test_in_transit_status_does_not_notify(db_session, shipment):
    channel = RecordingChannel()
    dispatcher = NotificationDispatcher([channel])
    provider = _FakeTrackingProvider(
        events=[
            TrackingProviderEvent(
                status="in_transit",
                description="Left facility",
                location="Leipzig",
                occurred_at=datetime(2026, 7, 2, tzinfo=UTC),
            )
        ]
    )

    TrackingSyncService(db_session, provider, dispatcher).sync_shipment(shipment)

    assert channel.sent == []
