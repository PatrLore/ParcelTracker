"""API tests for the version-check endpoint."""

from __future__ import annotations

import pytest

from app.schemas.system import VersionInfo


@pytest.fixture()
def auth_headers(client):
    client.post("/api/v1/users", json={"email": "system@example.com", "password": "password123"})
    login = client.post(
        "/api/v1/auth/login", json={"email": "system@example.com", "password": "password123"}
    )
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_get_version_requires_authentication(client):
    response = client.get("/api/v1/system/version")
    assert response.status_code == 401


def test_get_version_returns_service_result(client, auth_headers, monkeypatch):
    stub = VersionInfo(
        current_commit="aaaa111",
        latest_commit="bbbb222",
        update_available=True,
        compare_url="https://github.com/PatrLore/ParcelTracker/compare/aaaa111...bbbb222",
        check_failed=False,
    )
    monkeypatch.setattr("app.api.v1.endpoints.system.get_version_info", lambda client: stub)

    response = client.get("/api/v1/system/version", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == stub.model_dump()
