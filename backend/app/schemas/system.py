"""Version-check schema - deliberately read-only/informational, see
``app/services/version_service.py`` docstring for why there's no
auto-update endpoint."""

from __future__ import annotations

from pydantic import BaseModel


class VersionInfo(BaseModel):
    current_commit: str | None
    latest_commit: str | None
    update_available: bool
    compare_url: str | None
    check_failed: bool
