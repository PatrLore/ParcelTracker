"""Unit tests for StatisticsService's aggregate computations."""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest

from app.models.enums import ShipmentStatus
from app.models.order import Order
from app.repositories.order_repository import OrderRepository
from app.schemas.carrier import CarrierCreate
from app.schemas.order import OrderCreate
from app.schemas.shipment import ShipmentCreate, ShipmentUpdate
from app.schemas.user import UserCreate
from app.services.carrier_service import CarrierService
from app.services.order_service import OrderService
from app.services.shipment_service import ShipmentService
from app.services.statistics_service import StatisticsService
from app.services.user_service import UserService


@pytest.fixture()
def user(db_session):
    return UserService(db_session).create_user(
        UserCreate(email="stats-owner@example.com", password="password123")
    )


def test_monthly_counts_bucket_by_created_at(db_session, user):
    orders = OrderRepository(db_session)
    today = datetime.now(UTC)
    two_months_ago = today.replace(day=1) - _months(2)

    orders.add(Order(user_id=user.id, merchant="Amazon", currency="EUR", created_at=today))
    orders.add(
        Order(user_id=user.id, merchant="Zalando", currency="EUR", created_at=two_months_ago)
    )
    orders.commit()

    summary = StatisticsService(db_session).get_summary(user.id, months=12)

    counts_by_month = {entry.month: entry.count for entry in summary.parcels_per_month}
    assert counts_by_month[f"{today.year:04d}-{today.month:02d}"] == 1
    assert counts_by_month[f"{two_months_ago.year:04d}-{two_months_ago.month:02d}"] == 1
    assert len(summary.parcels_per_month) == 12


def _months(n: int):
    """A rough n-month timedelta, precise enough for bucketing tests."""
    from datetime import timedelta

    return timedelta(days=30 * n)


def test_top_merchant_and_carrier(db_session, user):
    order_service = OrderService(db_session)
    shipment_service = ShipmentService(db_session)
    carrier_service = CarrierService(db_session)

    ups = carrier_service.create_carrier(CarrierCreate(name="UPS"))
    dhl = carrier_service.create_carrier(CarrierCreate(name="DHL"))

    for _ in range(2):
        order = order_service.create_order(OrderCreate(merchant="Amazon"), user.id)
        shipment_service.create_shipment(
            ShipmentCreate(tracking_number=f"UPS-{order.id}", order_id=order.id)
        )
    order = order_service.create_order(OrderCreate(merchant="Zalando"), user.id)
    shipment_service.create_shipment(ShipmentCreate(tracking_number="DHL-1", order_id=order.id))

    # Attach carriers directly (ShipmentCreate schema has no carrier_id field).
    for shipment in shipment_service.list_shipments(user.id):
        shipment.carrier_id = ups.id if shipment.tracking_number.startswith("UPS") else dhl.id
    db_session.commit()

    summary = StatisticsService(db_session).get_summary(user.id)

    assert summary.top_merchant == "Amazon"
    assert summary.top_carrier == "UPS"


def test_average_delivery_days(db_session, user):
    order = OrderService(db_session).create_order(
        OrderCreate(merchant="Amazon", order_date=date(2026, 7, 1)), user.id
    )
    shipment_service = ShipmentService(db_session)
    shipment = shipment_service.create_shipment(
        ShipmentCreate(tracking_number="1Z1", order_id=order.id)
    )
    shipment_service.update_status(
        shipment.id,
        user.id,
        ShipmentUpdate(tracking_status=ShipmentStatus.DELIVERED, delivery_date=date(2026, 7, 4)),
    )

    summary = StatisticsService(db_session).get_summary(user.id)

    assert summary.average_delivery_days == 3.0
    assert summary.success_rate == 1.0


def test_delayed_rate_counts_current_and_historical_delays(db_session, user):
    order = OrderService(db_session).create_order(OrderCreate(merchant="Amazon"), user.id)
    shipment_service = ShipmentService(db_session)

    delayed = shipment_service.create_shipment(
        ShipmentCreate(tracking_number="A1", order_id=order.id)
    )
    shipment_service.update_status(
        delayed.id, user.id, ShipmentUpdate(tracking_status=ShipmentStatus.DELAYED)
    )
    fine = shipment_service.create_shipment(ShipmentCreate(tracking_number="A2", order_id=order.id))
    shipment_service.update_status(
        fine.id, user.id, ShipmentUpdate(tracking_status=ShipmentStatus.IN_TRANSIT)
    )

    summary = StatisticsService(db_session).get_summary(user.id)

    assert summary.total_shipments == 2
    assert summary.delayed_rate == 0.5


def test_summary_handles_no_data_gracefully(db_session, user):
    summary = StatisticsService(db_session).get_summary(user.id)

    assert summary.average_delivery_days is None
    assert summary.success_rate is None
    assert summary.top_merchant is None
    assert summary.top_carrier is None
    assert summary.delayed_rate == 0.0
    assert summary.total_shipments == 0
    assert len(summary.parcels_per_month) == 12
