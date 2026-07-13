"""Tests for the tracking-provider factory."""

from __future__ import annotations

import pytest
from tracking.providers.aftership import AfterShipProvider
from tracking.providers.factory import create_provider
from tracking.providers.seventeentrack import SeventeenTrackProvider
from tracking.providers.ship24 import Ship24Provider
from tracking.providers.trackingmore import TrackingMoreProvider


@pytest.mark.parametrize(
    ("name", "expected_type"),
    [
        ("seventeentrack", SeventeenTrackProvider),
        ("aftership", AfterShipProvider),
        ("trackingmore", TrackingMoreProvider),
        ("ship24", Ship24Provider),
    ],
)
def test_create_provider_returns_expected_type(name, expected_type):
    provider = create_provider(name, api_key="test-key")
    assert isinstance(provider, expected_type)


def test_create_provider_rejects_unknown_name():
    with pytest.raises(ValueError, match="Unknown tracking provider"):
        create_provider("not-a-real-provider", api_key="key")
