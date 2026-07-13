"""API tests for the statistics endpoint."""

from __future__ import annotations

import pytest


@pytest.fixture()
def auth_headers(client):
    client.post("/api/v1/users", json={"email": "stats@example.com", "password": "password123"})
    login = client.post(
        "/api/v1/auth/login", json={"email": "stats@example.com", "password": "password123"}
    )
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_statistics_summary_for_new_user(client, auth_headers):
    response = client.get("/api/v1/statistics/summary", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["total_shipments"] == 0
    assert body["average_delivery_days"] is None
    assert body["delayed_rate"] == 0.0
    assert len(body["parcels_per_month"]) == 12


def test_statistics_respects_months_query_param(client, auth_headers):
    response = client.get("/api/v1/statistics/summary?months=6", headers=auth_headers)

    assert response.status_code == 200
    assert len(response.json()["parcels_per_month"]) == 6


def test_statistics_require_authentication(client):
    response = client.get("/api/v1/statistics/summary")
    assert response.status_code == 401
