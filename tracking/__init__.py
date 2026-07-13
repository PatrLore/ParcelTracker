"""Carrier-agnostic tracking provider interface (Phase 3) and carrier
tracking-number detection (used starting Phase 2 by the email importer).

Concrete providers (17TRACK, AfterShip, TrackingMore, Ship24, direct carrier
APIs) implement :class:`TrackingProvider` so the backend never depends on a
specific tracking vendor - swapping the configured provider requires no
changes outside this package.
"""

from tracking.carriers import detect_carrier, find_tracking_numbers
from tracking.provider import TrackingProvider, TrackingProviderEvent

__all__ = [
    "TrackingProvider",
    "TrackingProviderEvent",
    "detect_carrier",
    "find_tracking_numbers",
]
