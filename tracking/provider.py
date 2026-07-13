"""The provider-agnostic tracking interface.

Every tracking backend (17TRACK, AfterShip, TrackingMore, Ship24, or a
carrier's own API) implements this interface. The service layer only ever
talks to :class:`TrackingProvider`, so switching providers is a
configuration change, not a code change.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class TrackingProviderEvent:
    """A single normalized tracking update returned by a provider."""

    status: str
    description: str | None
    location: str | None
    occurred_at: datetime


class TrackingProvider(ABC):
    """Interface every tracking provider integration must implement."""

    @abstractmethod
    def register(self, tracking_number: str, carrier_hint: str | None = None) -> None:
        """Start tracking a shipment with this provider."""

    @abstractmethod
    def update(self, tracking_number: str) -> list[TrackingProviderEvent]:
        """Fetch the latest tracking events for a shipment."""

    @abstractmethod
    def remove(self, tracking_number: str) -> None:
        """Stop tracking a shipment with this provider."""
