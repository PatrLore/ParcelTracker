"""API tests for registration, login and the current-user endpoint."""

from __future__ import annotations


def _register(client, email="api-user@example.com", password="password123"):
    return client.post("/api/v1/users", json={"email": email, "password": password})


def test_register_and_login_flow(client):
    register_response = _register(client)
    assert register_response.status_code == 201
    assert register_response.json()["email"] == "api-user@example.com"

    login_response = client.post(
        "/api/v1/auth/login", json={"email": "api-user@example.com", "password": "password123"}
    )
    assert login_response.status_code == 200
    tokens = login_response.json()
    assert tokens["token_type"] == "bearer"
    assert "access_token" in tokens

    me_response = client.get(
        "/api/v1/users/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "api-user@example.com"


def test_register_duplicate_email_returns_409(client):
    _register(client)
    duplicate = _register(client)
    assert duplicate.status_code == 409


def test_login_with_wrong_password_returns_401(client):
    _register(client)
    response = client.post(
        "/api/v1/auth/login", json={"email": "api-user@example.com", "password": "wrong"}
    )
    assert response.status_code == 401


def test_me_without_token_returns_401(client):
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401
