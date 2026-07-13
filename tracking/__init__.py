"""Carrier-agnostic tracking provider interface (Phase 3).

Concrete providers (17TRACK, AfterShip, TrackingMore, Ship24, direct carrier
APIs) implement :class:`TrackingProvider` so the backend never depends on a
specific tracking vendor - swapping the configured provider requires no
changes outside this package.
"""

from tracking.provider import TrackingProvider, TrackingProviderEvent

__all__ = ["TrackingProvider", "TrackingProviderEvent"]
