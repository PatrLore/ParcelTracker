"""Tests for MqttPublishService's aggregate-count publishing."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from app.models.enums import ShipmentStatus
from app.schemas.order import OrderCreate
from app.schemas.shipment import ShipmentCreate, ShipmentUpdate
from app.schemas.user import UserCreate
from app.services.mqtt_publish_service import MqttPublishService
from app.services.order_service import OrderService
from app.services.shipment_service import ShipmentService
from app.services.user_service import UserService


class FakePublisher:
    def __init__(self) -> None:
        self.connected = False
        self.disconnected = False
        self.discovery_published = False
        self.published_values: dict | None = None

    def connect(self) -> None:
        self.connected = True

    def disconnect(self) -> None:
        self.disconnected = True

    def publish_discovery(self) -> None:
        self.discovery_published = True

    def publish_state(self, values: dict) -> None:
        self.published_values = values


@pytest.fixture()
def user(db_session):
    return UserService(db_session).create_user(
        UserCreate(email="mqtt-owner@example.com", password="password123")
    )


def test_publish_reports_aggregate_counts(db_session, user):
    order = OrderService(db_session).create_order(OrderCreate(merchant="Amazon"), user.id)
    shipment_service = ShipmentService(db_session)

    in_transit = shipment_service.create_shipment(
        ShipmentCreate(tracking_number="A1", order_id=order.id)
    )
    shipment_service.update_status(
        in_transit.id, user.id, ShipmentUpdate(tracking_status=ShipmentStatus.IN_TRANSIT)
    )

    delivered = shipment_service.create_shipment(
        ShipmentCreate(tracking_number="A2", order_id=order.id, delivery_date=date.today())
    )
    shipment_service.update_status(
        delivered.id, user.id, ShipmentUpdate(tracking_status=ShipmentStatus.DELIVERED)
    )

    upcoming = shipment_service.create_shipment(
        ShipmentCreate(
            tracking_number="A3",
            order_id=order.id,
            estimated_delivery_date=date.today() + timedelta(days=2),
        )
    )
    shipment_service.update_status(
        upcoming.id, user.id, ShipmentUpdate(tracking_status=ShipmentStatus.OUT_FOR_DELIVERY)
    )

    publisher = FakePublisher()
    MqttPublishService(db_session, publisher).publish()

    assert publisher.connected is True
    assert publisher.disconnected is True
    assert publisher.discovery_published is True
    assert publisher.published_values["total"] == 3
    assert publisher.published_values["in_transit"] == 2  # IN_TRANSIT + OUT_FOR_DELIVERY
    assert publisher.published_values["delivered_today"] == 1
    assert (
        publisher.published_values["next_delivery"]
        == (date.today() + timedelta(days=2)).isoformat()
    )
