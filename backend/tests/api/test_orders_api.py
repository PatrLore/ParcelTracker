"""API tests for the orders and dashboard endpoints."""

from __future__ import annotations

import pytest


@pytest.fixture()
def auth_headers(client):
    client.post("/api/v1/users", json={"email": "orders@example.com", "password": "password123"})
    login = client.post(
        "/api/v1/auth/login", json={"email": "orders@example.com", "password": "password123"}
    )
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_and_list_orders(client, auth_headers):
    create_response = client.post(
        "/api/v1/orders",
        json={"merchant": "Amazon", "order_number": "AMZ-123"},
        headers=auth_headers,
    )
    assert create_response.status_code == 201
    order_id = create_response.json()["id"]

    list_response = client.get("/api/v1/orders", headers=auth_headers)
    assert list_response.status_code == 200
    assert any(order["id"] == order_id for order in list_response.json())


def test_orders_require_authentication(client):
    response = client.get("/api/v1/orders")
    assert response.status_code == 401


def test_get_missing_order_returns_404(client, auth_headers):
    response = client.get("/api/v1/orders/999999", headers=auth_headers)
    assert response.status_code == 404


def test_dashboard_summary_empty_for_new_user(client, auth_headers):
    response = client.get("/api/v1/dashboard/summary", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["in_transit"] == 0
    assert body["recent_shipments"] == []


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_archive_and_unarchive_order(client, auth_headers):
    create_response = client.post(
        "/api/v1/orders", json={"merchant": "Amazon"}, headers=auth_headers
    )
    order_id = create_response.json()["id"]

    archive_response = client.post(f"/api/v1/orders/{order_id}/archive", headers=auth_headers)
    assert archive_response.status_code == 200
    assert archive_response.json()["archived"] is True

    unarchive_response = client.post(
        f"/api/v1/orders/{order_id}/archive", json={"archived": False}, headers=auth_headers
    )
    assert unarchive_response.status_code == 200
    assert unarchive_response.json()["archived"] is False


def test_archive_missing_order_returns_404(client, auth_headers):
    response = client.post("/api/v1/orders/999999/archive", headers=auth_headers)
    assert response.status_code == 404
