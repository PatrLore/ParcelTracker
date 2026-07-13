"""API tests for shipment endpoints, including tracking refresh."""

from __future__ import annotations

import pytest


@pytest.fixture()
def auth_headers(client):
    client.post("/api/v1/users", json={"email": "shipments@example.com", "password": "password123"})
    login = client.post(
        "/api/v1/auth/login", json={"email": "shipments@example.com", "password": "password123"}
    )
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def order_id(client, auth_headers):
    response = client.post("/api/v1/orders", json={"merchant": "Amazon"}, headers=auth_headers)
    return response.json()["id"]


def test_create_and_get_shipment(client, auth_headers, order_id):
    create_response = client.post(
        "/api/v1/shipments",
        json={"tracking_number": "1Z999AA10123456784", "order_id": order_id},
        headers=auth_headers,
    )
    assert create_response.status_code == 201
    shipment_id = create_response.json()["id"]

    get_response = client.get(f"/api/v1/shipments/{shipment_id}", headers=auth_headers)
    assert get_response.status_code == 200
    assert get_response.json()["tracking_number"] == "1Z999AA10123456784"


def test_refresh_tracking_without_configured_provider_returns_501(client, auth_headers, order_id):
    create_response = client.post(
        "/api/v1/shipments",
        json={"tracking_number": "1Z999AA10123456784", "order_id": order_id},
        headers=auth_headers,
    )
    shipment_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/shipments/{shipment_id}/refresh-tracking", headers=auth_headers
    )

    assert response.status_code == 501


def test_shipments_require_authentication(client):
    response = client.get("/api/v1/shipments")
    assert response.status_code == 401
