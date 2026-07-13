"""Builds the tracking provider configured in ``config.yaml``.

The only other place backend code touches ``tracking.providers`` is
:mod:`app.services.tracking_sync_service` - both go through this factory so
there's a single place that reads ``tracking_provider.*`` settings.
"""

from __future__ import annotations

from tracking.provider import TrackingProvider
from tracking.providers.factory import create_provider

from app.config import get_settings


def get_configured_tracking_provider() -> TrackingProvider | None:
    """Returns the configured provider, or ``None`` if none is configured."""
    settings = get_settings().tracking_provider
    if settings.name == "none":
        return None
    return create_provider(settings.name, settings.api_key)
