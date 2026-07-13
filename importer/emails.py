"""The raw, mailbox-agnostic representation of a fetched email."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class RawEmail:
    """A single email as fetched from a mailbox, before merchant parsing."""

    uid: int
    message_id: str
    subject: str
    sender: str
    received_at: datetime
    text_body: str
    html_body: str = ""
    attachments: list[str] = field(default_factory=list)

    @property
    def body(self) -> str:
        """The text body, falling back to a tag-stripped HTML body."""
        return self.text_body or self.html_body
