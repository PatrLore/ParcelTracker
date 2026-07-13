"""The channel-agnostic notification payload."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class NotificationMessage:
    """A single notification to deliver through one or more channels."""

    event: str
    title: str
    body: str
    metadata: dict[str, str] = field(default_factory=dict)
