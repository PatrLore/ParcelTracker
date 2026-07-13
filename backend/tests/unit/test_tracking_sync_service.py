"""Unit tests for TrackingSyncService: provider events -> Shipment/TrackingEvent.

Uses a fake, in-memory TrackingProvider (no real HTTP calls) so these tests
are fast and hermetic - only the backend <-> tracking integration is
exercised.
"""

from __future__ import annotations

from datetime import UTC, datetime

import httpx
import pytest
from tracking.provider import TrackingProvider, TrackingProviderEvent

from app.models.enums import OrderStatus, ShipmentStatus
from app.schemas.order import OrderCreate
from app.schemas.shipment import ShipmentCreate
from app.schemas.user import UserCreate
from app.services.order_service import OrderService
from app.services.shipment_service import ShipmentService
from app.services.tracking_sync_service import TrackingSyncService
from app.services.user_service import UserService


class FakeProvider(TrackingProvider):
    def __init__(self, events: list[TrackingProviderEvent]) -> None:
        self._events = events
        self.registered: list[str] = []
        self.removed: list[str] = []

    def register(self, tracking_number: str, carrier_hint: str | None = None) -> None:
        self.registered.append(tracking_number)

    def update(self, tracking_number: str) -> list[TrackingProviderEvent]:
        return self._events

    def remove(self, tracking_number: str) -> None:
        self.removed.append(tracking_number)


@pytest.fixture()
def shipment(db_session):
    user = UserService(db_session).create_user(
        UserCreate(email="tracking-owner@example.com", password="password123")
    )
    order = OrderService(db_session).create_order(
        OrderCreate(merchant="Amazon", status=OrderStatus.SHIPPED), user.id
    )
    return ShipmentService(db_session).create_shipment(
        ShipmentCreate(tracking_number="1Z999AA10123456784", order_id=order.id)
    )


def test_sync_shipment_registers_once(db_session, shipment):
    provider = FakeProvider(events=[])
    service = TrackingSyncService(db_session, provider)

    service.sync_shipment(shipment)
    service.sync_shipment(shipment)

    assert provider.registered == ["1Z999AA10123456784"]  # only once
    assert shipment.tracking_registered is True


def test_sync_shipment_appends_new_events_and_updates_status(db_session, shipment):
    provider = FakeProvider(
        events=[
            TrackingProviderEvent(
                status="in_transit",
                description="Left facility",
                location="Leipzig",
                occurred_at=datetime(2026, 7, 1, tzinfo=UTC),
            ),
            TrackingProviderEvent(
                status="delivered",
                description="Delivered",
                location="Berlin",
                occurred_at=datetime(2026, 7, 3, tzinfo=UTC),
            ),
        ]
    )
    service = TrackingSyncService(db_session, provider)

    updated = service.sync_shipment(shipment)

    assert updated.tracking_status == ShipmentStatus.DELIVERED
    assert updated.delivery_date == datetime(2026, 7, 3, tzinfo=UTC).date()
    assert len(updated.tracking_events) == 2
    # Naive UTC: DateTime(timezone=True) round-trips as naive on SQLite.
    assert updated.last_update == datetime(2026, 7, 3)


def test_sync_shipment_does_not_duplicate_known_events(db_session, shipment):
    event = TrackingProviderEvent(
        status="in_transit",
        description="Left facility",
        location="Leipzig",
        occurred_at=datetime(2026, 7, 1, tzinfo=UTC),
    )
    provider = FakeProvider(events=[event])
    service = TrackingSyncService(db_session, provider)

    service.sync_shipment(shipment)
    service.sync_shipment(shipment)

    assert len(shipment.tracking_events) == 1


def test_sync_shipment_falls_back_to_in_transit_for_unknown_status(db_session, shipment):
    provider = FakeProvider(
        events=[
            TrackingProviderEvent(
                status="some-vendor-specific-code",
                description="Unrecognized",
                location=None,
                occurred_at=datetime(2026, 7, 1, tzinfo=UTC),
            )
        ]
    )
    service = TrackingSyncService(db_session, provider)

    updated = service.sync_shipment(shipment)

    assert updated.tracking_status == ShipmentStatus.IN_TRANSIT


def test_sync_due_shipments_skips_terminal_shipments(db_session, shipment):
    delivered_event = TrackingProviderEvent(
        status="delivered",
        description="Delivered",
        location="Berlin",
        occurred_at=datetime(2026, 7, 1, tzinfo=UTC),
    )
    provider = FakeProvider(events=[delivered_event])
    service = TrackingSyncService(db_session, provider)

    first_pass = service.sync_due_shipments()
    second_pass = service.sync_due_shipments()

    assert first_pass == 1
    assert second_pass == 0  # now DELIVERED -> terminal -> excluded


def test_sync_due_shipments_continues_after_one_shipment_fails(db_session, shipment):
    class FlakyProvider(FakeProvider):
        def update(self, tracking_number: str) -> list[TrackingProviderEvent]:
            raise httpx.ConnectError("boom", request=httpx.Request("GET", "https://example.com"))

    service = TrackingSyncService(db_session, FlakyProvider(events=[]))

    synced = service.sync_due_shipments()

    assert synced == 0  # the one shipment failed, but sync_due_shipments did not raise
