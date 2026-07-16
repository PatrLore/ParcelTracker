"""Tests for regex-based carrier tracking-number detection."""

from __future__ import annotations

from tracking.carriers import detect_carrier, find_tracking_numbers


def test_detect_ups():
    assert detect_carrier("1Z999AA10123456784") == "UPS"


def test_detect_amazon_logistics():
    assert detect_carrier("TBA123456789012") == "Amazon Logistics"


def test_detect_deutsche_post():
    assert detect_carrier("RR123456789DE") == "Deutsche Post"


def test_detect_royal_mail():
    assert detect_carrier("AB123456789GB") == "Royal Mail"


def test_detect_postnl():
    assert detect_carrier("3SABCDEFGHIJK") == "PostNL"


def test_detect_cainiao():
    assert detect_carrier("LP00123456789012") == "Cainiao"


def test_detect_yunexpress():
    assert detect_carrier("YT1234567890123456") == "YunExpress"


def test_detect_unknown_format_returns_none():
    assert detect_carrier("not-a-tracking-number") is None


def test_find_tracking_numbers_in_free_text():
    text = (
        "Ihre Sendung ist unterwegs. Trackingnummer: 1Z999AA10123456784. "
        "Vielen Dank fuer Ihren Einkauf. Referenz: TBA123456789012"
    )
    found = find_tracking_numbers(text)

    assert found["1Z999AA10123456784"] == "UPS"
    assert found["TBA123456789012"] == "Amazon Logistics"


def test_find_tracking_numbers_prefers_carrier_named_in_text():
    """A DHL notification's own tracking number (20 digits) shouldn't lose
    out to an unrelated 11-digit number elsewhere in the text (e.g. a
    customer ID) that coincidentally matches GLS's bare-digit pattern -
    GLS is checked before DHL in _DETECTION_ORDER, so without this
    disambiguation the false positive would be found first."""
    text = (
        "Ihre DHL Sendung ist unterwegs. Kundennummer: 12345678901. "
        "Sendungsstatus einsehen: 00340435093806820124"
    )

    found = find_tracking_numbers(text)

    assert found == {"00340435093806820124": "DHL"}


def test_find_tracking_numbers_keeps_ambiguous_matches_when_no_carrier_named():
    text = "Referenz: 12345678901. Sendungsnummer: 00340435093806820124"

    found = find_tracking_numbers(text)

    assert found["12345678901"] == "GLS"
    assert found["00340435093806820124"] == "DHL"
