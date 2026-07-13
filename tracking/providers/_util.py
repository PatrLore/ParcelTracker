"""Small helpers shared by the concrete provider implementations."""

from __future__ import annotations

from datetime import UTC, datetime


def parse_timestamp(value: str | None) -> datetime:
    """Parse an ISO-8601-ish timestamp, falling back to "now" if missing/invalid.

    Providers occasionally omit a timestamp on very recent events; falling
    back to now keeps the event visible instead of dropping it.
    """
    if not value:
        return datetime.now(UTC)
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return datetime.now(UTC)
