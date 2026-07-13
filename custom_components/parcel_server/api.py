"""Thin async client for the Parcel Server REST API (``/api/v1``).

Deliberately free of any ``homeassistant.*`` import so it can be unit
tested with a plain aiohttp session and no Home Assistant runtime - see
``integrations/home_assistant/tests``.
"""

from __future__ import annotations

from typing import Any

import aiohttp


class ParcelServerError(Exception):
    """Base class for all client errors."""


class ParcelServerAuthError(ParcelServerError):
    """Raised when login fails or the session token has been rejected twice."""


class ParcelServerConnectionError(ParcelServerError):
    """Raised on network failures or non-2xx/401 responses."""


class ParcelServerApiClient:
    """Talks to a Parcel Server backend on behalf of one configured account."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        base_url: str,
        email: str,
        password: str,
        verify_ssl: bool = True,
    ) -> None:
        self._session = session
        self._base_url = base_url.rstrip("/")
        self._email = email
        self._password = password
        self._verify_ssl = verify_ssl
        self._access_token: str | None = None

    async def async_login(self) -> None:
        """Authenticates and stores the access token for subsequent requests."""
        try:
            response = await self._session.post(
                f"{self._base_url}/api/v1/auth/login",
                json={"email": self._email, "password": self._password},
                ssl=self._verify_ssl,
            )
        except aiohttp.ClientError as exc:
            raise ParcelServerConnectionError(str(exc)) from exc

        if response.status == 401:
            raise ParcelServerAuthError("Invalid email or password")
        if response.status != 200:
            raise ParcelServerConnectionError(f"Login failed with status {response.status}")

        payload = await response.json()
        self._access_token = payload["access_token"]

    async def _request(
        self, method: str, path: str, retry_on_auth_error: bool = True, **kwargs: Any
    ) -> Any:
        if self._access_token is None:
            await self.async_login()

        headers = {"Authorization": f"Bearer {self._access_token}"}
        try:
            response = await self._session.request(
                method,
                f"{self._base_url}{path}",
                headers=headers,
                ssl=self._verify_ssl,
                **kwargs,
            )
        except aiohttp.ClientError as exc:
            raise ParcelServerConnectionError(str(exc)) from exc

        if response.status == 401 and retry_on_auth_error:
            # Access token expired/invalid - log in again once and retry.
            await self.async_login()
            return await self._request(method, path, retry_on_auth_error=False, **kwargs)

        if response.status >= 400:
            raise ParcelServerConnectionError(
                f"{method} {path} failed with status {response.status}"
            )

        if response.content_type == "application/json":
            return await response.json()
        return None

    async def async_get_dashboard_summary(self) -> dict[str, Any]:
        return await self._request("GET", "/api/v1/dashboard/summary")

    async def async_get_statistics_summary(self, months: int = 12) -> dict[str, Any]:
        return await self._request("GET", "/api/v1/statistics/summary", params={"months": months})

    async def async_list_orders(self, offset: int = 0, limit: int = 100) -> list[dict[str, Any]]:
        return await self._request(
            "GET", "/api/v1/orders", params={"offset": offset, "limit": limit}
        )

    async def async_refresh_tracking(self, shipment_id: int) -> dict[str, Any]:
        return await self._request("POST", f"/api/v1/shipments/{shipment_id}/refresh-tracking")

    async def async_archive_order(self, order_id: int, archived: bool = True) -> dict[str, Any]:
        return await self._request(
            "POST", f"/api/v1/orders/{order_id}/archive", json={"archived": archived}
        )

    async def async_send_notification(
        self, title: str, body: str, event: str = "manual"
    ) -> dict[str, Any]:
        return await self._request(
            "POST",
            "/api/v1/notifications/send",
            json={"title": title, "body": body, "event": event},
        )
