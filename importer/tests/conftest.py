"""Shared fixtures for importer tests."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from importer.emails import RawEmail


@pytest.fixture()
def make_email():
    def _make(
        sender: str,
        subject: str,
        body: str,
        uid: int = 1,
        message_id: str = "<test@example.com>",
        received_at: datetime | None = None,
    ) -> RawEmail:
        return RawEmail(
            uid=uid,
            message_id=message_id,
            subject=subject,
            sender=sender,
            received_at=received_at or datetime(2026, 7, 1, tzinfo=UTC),
            text_body=body,
        )

    return _make
