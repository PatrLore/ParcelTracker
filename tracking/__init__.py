"""Carrier-agnostic tracking provider interface and carrier tracking-number
detection.

Concrete providers (17TRACK, AfterShip, TrackingMore, Ship24 - see
``tracking.providers``) implement :class:`TrackingProvider` so the backend
never depends on a specific tracking vendor - swapping the configured
provider requires no changes outside this package.
"""

from tracking.carriers import detect_carrier, find_tracking_numbers
from tracking.provider import TrackingProvider, TrackingProviderEvent
from tracking.providers.factory import create_provider

__all__ = [
    "TrackingProvider",
    "TrackingProviderEvent",
    "create_provider",
    "detect_carrier",
    "find_tracking_numbers",
]
