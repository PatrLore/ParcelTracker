"""Google OAuth2 device-code flow for IMAP access to Gmail mailboxes.

An alternative to a Gmail app password (which still works for personal
Gmail accounts, unlike Outlook.com/Hotmail - see ``docs/mailboxes.md``):
useful for accounts without 2-Step Verification enabled (a prerequisite
for app passwords), or for anyone who'd rather not generate one.

Mirrors ``app.services.oauth_microsoft`` structurally (device-code grant,
RFC 8628, no public HTTPS redirect URL needed), but against Google's
endpoints, which differ in two ways:

- Google's device-code response field is ``verification_url`` (Microsoft:
  ``verification_uri``) - normalized to ``verification_uri`` on our
  :class:`DeviceFlow` for a uniform frontend/API shape either way.
- Google's token endpoint requires ``client_secret`` even for this
  "TV and Limited Input devices" client type, unlike Microsoft's public
  client flow.

Pending/completed flows are kept in-memory (module-level dicts), which is
fine because Parcel Server's backend runs as a single Uvicorn process (see
``entrypoint.sh``) - there is no multi-worker fan-out that would miss them.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass

import httpx

from app.config import get_settings

_AUTHORITY = "https://oauth2.googleapis.com"
_SCOPE = "https://mail.google.com/"
#: How long a completed-but-not-yet-finalized flow's tokens are kept around.
_COMPLETED_FLOW_TTL_SECONDS = 600


class DeviceFlowExpiredError(Exception):
    """The device code expired before the user finished signing in."""


class DeviceFlowFailedError(Exception):
    """Google rejected the device-code sign-in (declined, revoked, ...)."""


class DeviceFlowNotFoundError(Exception):
    """No pending or completed flow exists for this flow_id (or wrong owner)."""


@dataclass
class DeviceFlow:
    flow_id: str
    user_id: int
    device_code: str
    user_code: str
    verification_uri: str
    expires_at: float
    interval: int


@dataclass
class TokenResult:
    access_token: str
    refresh_token: str
    expires_in: int


@dataclass
class _CompletedFlow:
    user_id: int
    tokens: TokenResult
    expires_at: float


_pending_flows: dict[str, DeviceFlow] = {}
_completed_flows: dict[str, _CompletedFlow] = {}


def _purge_expired() -> None:
    now = time.monotonic()
    for flow_id in [fid for fid, flow in _pending_flows.items() if now > flow.expires_at]:
        _pending_flows.pop(flow_id, None)
    for flow_id in [fid for fid, flow in _completed_flows.items() if now > flow.expires_at]:
        _completed_flows.pop(flow_id, None)


def start_device_flow(client: httpx.Client, user_id: int) -> DeviceFlow:
    _purge_expired()
    settings = get_settings().google_oauth
    response = client.post(
        f"{_AUTHORITY}/device/code",
        data={"client_id": settings.client_id, "scope": _SCOPE},
    )
    response.raise_for_status()
    payload = response.json()
    flow = DeviceFlow(
        flow_id=uuid.uuid4().hex,
        user_id=user_id,
        device_code=payload["device_code"],
        user_code=payload["user_code"],
        verification_uri=payload["verification_url"],
        expires_at=time.monotonic() + payload.get("expires_in", 1800),
        interval=payload.get("interval", 5),
    )
    _pending_flows[flow.flow_id] = flow
    return flow


def poll_device_flow(client: httpx.Client, flow_id: str, user_id: int) -> bool:
    """Returns True once sign-in has completed. Raises
    :class:`DeviceFlowExpiredError`/:class:`DeviceFlowFailedError`/:class:`DeviceFlowNotFoundError`
    otherwise, and returns False while sign-in is still pending."""
    if flow_id in _completed_flows:
        if _completed_flows[flow_id].user_id != user_id:
            raise DeviceFlowNotFoundError
        return True

    flow = _pending_flows.get(flow_id)
    if flow is None or flow.user_id != user_id:
        raise DeviceFlowNotFoundError

    if time.monotonic() > flow.expires_at:
        _pending_flows.pop(flow_id, None)
        raise DeviceFlowExpiredError

    settings = get_settings().google_oauth
    response = client.post(
        f"{_AUTHORITY}/token",
        data={
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            "client_id": settings.client_id,
            "client_secret": settings.client_secret,
            "device_code": flow.device_code,
        },
    )
    payload = response.json()

    if response.status_code == 200:
        _pending_flows.pop(flow_id, None)
        _completed_flows[flow_id] = _CompletedFlow(
            user_id=user_id,
            tokens=TokenResult(
                access_token=payload["access_token"],
                refresh_token=payload["refresh_token"],
                expires_in=payload["expires_in"],
            ),
            expires_at=time.monotonic() + _COMPLETED_FLOW_TTL_SECONDS,
        )
        return True

    error = payload.get("error")
    if error == "authorization_pending" or error == "slow_down":
        return False
    _pending_flows.pop(flow_id, None)
    if error == "expired_token":
        raise DeviceFlowExpiredError
    raise DeviceFlowFailedError(payload.get("error_description", error or "unknown error"))


def take_completed_tokens(flow_id: str, user_id: int) -> TokenResult:
    """Consumes (pops) the tokens from a completed flow. Raises
    :class:`DeviceFlowNotFoundError` if there is none for this id/user."""
    _purge_expired()
    completed = _completed_flows.get(flow_id)
    if completed is None or completed.user_id != user_id:
        raise DeviceFlowNotFoundError
    del _completed_flows[flow_id]
    return completed.tokens


def refresh_access_token(client: httpx.Client, refresh_token: str) -> TokenResult:
    settings = get_settings().google_oauth
    response = client.post(
        f"{_AUTHORITY}/token",
        data={
            "grant_type": "refresh_token",
            "client_id": settings.client_id,
            "client_secret": settings.client_secret,
            "refresh_token": refresh_token,
        },
    )
    response.raise_for_status()
    payload = response.json()
    return TokenResult(
        access_token=payload["access_token"],
        # Google doesn't always return a new refresh token on refresh; fall
        # back to the old one when it doesn't.
        refresh_token=payload.get("refresh_token", refresh_token),
        expires_in=payload["expires_in"],
    )
