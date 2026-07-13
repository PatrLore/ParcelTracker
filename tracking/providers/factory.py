"""Builds the configured :class:`~tracking.provider.TrackingProvider`.

The only place in the application that needs to know all provider classes
exist - everything else depends on the ``TrackingProvider`` interface.
"""

from __future__ import annotations

from tracking.provider import TrackingProvider
from tracking.providers.aftership import AfterShipProvider
from tracking.providers.seventeentrack import SeventeenTrackProvider
from tracking.providers.ship24 import Ship24Provider
from tracking.providers.trackingmore import TrackingMoreProvider

_PROVIDERS: dict[str, type[TrackingProvider]] = {
    "seventeentrack": SeventeenTrackProvider,
    "aftership": AfterShipProvider,
    "trackingmore": TrackingMoreProvider,
    "ship24": Ship24Provider,
}


def create_provider(name: str, api_key: str) -> TrackingProvider:
    """Instantiate the tracking provider named ``name``.

    Raises ``ValueError`` for "none" or any unrecognized name - callers that
    treat "no provider configured" as a valid state should check for that
    before calling this.
    """
    try:
        provider_cls = _PROVIDERS[name]
    except KeyError as exc:
        raise ValueError(f"Unknown tracking provider: {name!r}") from exc
    return provider_cls(api_key)
