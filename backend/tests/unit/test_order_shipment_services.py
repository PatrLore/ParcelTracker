"""Unit tests for order/shipment services and the dashboard aggregation."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from app.models.enums import OrderStatus, ShipmentStatus
from app.schemas.order import OrderCreate, OrderUpdate
from app.schemas.shipment import ShipmentCreate, ShipmentUpdate
from app.schemas.user import UserCreate
from app.services.dashboard_service import DashboardService
from app.services.exceptions import NotFoundError
from app.services.order_service import OrderService
from app.services.shipment_service import ShipmentService
from app.services.user_service import UserService


@pytest.fixture()
def user(db_session):
    return UserService(db_session).create_user(
        UserCreate(email="owner@example.com", password="password123")
    )


def test_order_lifecycle(db_session, user):
    service = OrderService(db_session)
    order = service.create_order(
        OrderCreate(merchant="Amazon", order_number="AMZ-1", status=OrderStatus.CONFIRMED), user.id
    )
    assert order.id is not None

    fetched = service.get_order(order.id, user.id)
    assert fetched.merchant == "Amazon"

    updated = service.update_order(order.id, OrderUpdate(status=OrderStatus.SHIPPED), user.id)
    assert updated.status == OrderStatus.SHIPPED

    service.delete_order(order.id, user.id)
    with pytest.raises(NotFoundError):
        service.get_order(order.id, user.id)


def test_order_scoped_to_owner(db_session, user):
    other = UserService(db_session).create_user(
        UserCreate(email="other@example.com", password="password123")
    )
    service = OrderService(db_session)
    order = service.create_order(OrderCreate(merchant="Zalando"), user.id)

    with pytest.raises(NotFoundError):
        service.get_order(order.id, other.id)


def test_shipment_status_update_records_history(db_session, user):
    order = OrderService(db_session).create_order(OrderCreate(merchant="Otto"), user.id)
    shipment = ShipmentService(db_session).create_shipment(
        ShipmentCreate(tracking_number="1Z999", order_id=order.id)
    )

    updated = ShipmentService(db_session).update_status(
        shipment.id, user.id, ShipmentUpdate(tracking_status=ShipmentStatus.IN_TRANSIT)
    )

    assert updated.tracking_status == ShipmentStatus.IN_TRANSIT
    assert len(updated.tracking_events) == 1
    assert updated.last_update is not None


def test_dashboard_summary_counts_by_status(db_session, user):
    order = OrderService(db_session).create_order(OrderCreate(merchant="IKEA"), user.id)
    shipment_service = ShipmentService(db_session)

    in_transit = shipment_service.create_shipment(
        ShipmentCreate(tracking_number="A1", order_id=order.id)
    )
    shipment_service.update_status(
        in_transit.id, user.id, ShipmentUpdate(tracking_status=ShipmentStatus.IN_TRANSIT)
    )

    delivered_today = shipment_service.create_shipment(
        ShipmentCreate(tracking_number="A2", order_id=order.id, delivery_date=date.today())
    )
    shipment_service.update_status(
        delivered_today.id, user.id, ShipmentUpdate(tracking_status=ShipmentStatus.DELIVERED)
    )

    expected_tomorrow = shipment_service.create_shipment(
        ShipmentCreate(
            tracking_number="A3",
            order_id=order.id,
            estimated_delivery_date=date.today() + timedelta(days=1),
        )
    )
    shipment_service.update_status(
        expected_tomorrow.id,
        user.id,
        ShipmentUpdate(tracking_status=ShipmentStatus.OUT_FOR_DELIVERY),
    )

    summary = DashboardService(db_session).get_summary(user.id)

    assert summary.in_transit == 2  # IN_TRANSIT + OUT_FOR_DELIVERY
    assert summary.delivered_today == 1
    assert summary.expected_tomorrow == 1
    assert len(summary.recent_shipments) == 3


def test_archiving_order_excludes_its_shipments_from_dashboard(db_session, user):
    order = OrderService(db_session).create_order(OrderCreate(merchant="IKEA"), user.id)
    shipment_service = ShipmentService(db_session)
    shipment = shipment_service.create_shipment(
        ShipmentCreate(tracking_number="A1", order_id=order.id)
    )
    shipment_service.update_status(
        shipment.id, user.id, ShipmentUpdate(tracking_status=ShipmentStatus.IN_TRANSIT)
    )

    before = DashboardService(db_session).get_summary(user.id)
    assert before.in_transit == 1

    archived = OrderService(db_session).set_archived(order.id, user.id, True)
    assert archived.archived is True

    after = DashboardService(db_session).get_summary(user.id)
    assert after.in_transit == 0
    assert after.recent_shipments == []

    unarchived = OrderService(db_session).set_archived(order.id, user.id, False)
    assert unarchived.archived is False
    assert DashboardService(db_session).get_summary(user.id).in_transit == 1
