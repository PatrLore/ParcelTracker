"""Compares the running container's commit against the latest commit on
GitHub - informational only. Deliberately does not (and will not) execute
``git pull``/``docker compose`` itself: doing that from inside the backend
container would require mounting the host's Docker socket into it, which
is equivalent to root on the host for anyone who can reach the API. See
``docs/roadmap.md``."""

from __future__ import annotations

import logging
import time

import httpx

from app.core.version import get_running_commit
from app.schemas.system import VersionInfo

logger = logging.getLogger(__name__)

_REPO = "PatrLore/ParcelTracker"
_LATEST_COMMIT_URL = f"https://api.github.com/repos/{_REPO}/commits/main"
_CACHE_TTL_SECONDS = 600

_cache: dict[str, tuple[float, str | None]] = {}


def _fetch_latest_commit(client: httpx.Client) -> str | None:
    cached = _cache.get("latest_commit")
    if cached and time.monotonic() - cached[0] < _CACHE_TTL_SECONDS:
        return cached[1]

    try:
        response = client.get(_LATEST_COMMIT_URL, headers={"Accept": "application/vnd.github+json"})
        response.raise_for_status()
        sha = response.json()["sha"]
    except (httpx.HTTPError, KeyError, ValueError):
        logger.warning("Could not check for updates against %s", _LATEST_COMMIT_URL, exc_info=True)
        return None

    _cache["latest_commit"] = (time.monotonic(), sha)
    return sha


def get_version_info(client: httpx.Client) -> VersionInfo:
    current = get_running_commit()
    latest = _fetch_latest_commit(client)

    if current is None or latest is None:
        return VersionInfo(
            current_commit=current,
            latest_commit=latest,
            update_available=False,
            compare_url=None,
            check_failed=latest is None,
        )

    return VersionInfo(
        current_commit=current,
        latest_commit=latest,
        update_available=current != latest,
        compare_url=f"https://github.com/{_REPO}/compare/{current}...{latest}",
        check_failed=False,
    )
