"""Modular, regex-based tracking-number detection.

Each carrier is registered independently in ``CARRIER_PATTERNS``; adding
support for a new carrier means adding one entry here, nothing else.
Patterns are deliberately conservative (anchored, fixed-length where the
carrier's format allows it) to keep false positives low when scanning free
text such as an email body.
"""

from __future__ import annotations

import re

CARRIER_PATTERNS: dict[str, re.Pattern[str]] = {
    "DHL": re.compile(r"\b(\d{12}|\d{10}|\d{20})\b"),
    "DHL Express": re.compile(r"\b(\d{10})\b"),
    "Deutsche Post": re.compile(r"\b([A-Z]{2}\d{9}DE)\b"),
    "UPS": re.compile(r"\b(1Z[0-9A-Z]{16})\b"),
    "DPD": re.compile(r"\b(\d{14})\b"),
    "GLS": re.compile(r"\b(\d{11})\b"),
    "Hermes": re.compile(r"\b(\d{14}|[A-Z]{1}\d{10})\b"),
    "FedEx": re.compile(r"\b(\d{12}|\d{15}|\d{20})\b"),
    "USPS": re.compile(r"\b(9\d{21}|9\d{25})\b"),
    "Cainiao": re.compile(r"\b(LP\d{14,20})\b"),
    "YunExpress": re.compile(r"\b(YT\d{16,18})\b"),
    "Amazon Logistics": re.compile(r"\b(TBA\d{12})\b"),
    "Royal Mail": re.compile(r"\b([A-Z]{2}\d{9}GB)\b"),
    "PostNL": re.compile(r"\b(3S[A-Z0-9]{11,13})\b"),
}

# More specific/unambiguous formats first, so a number matching several
# generic digit-length patterns still resolves to its most likely carrier.
_DETECTION_ORDER: tuple[str, ...] = (
    "UPS",
    "Amazon Logistics",
    "Cainiao",
    "YunExpress",
    "PostNL",
    "Deutsche Post",
    "Royal Mail",
    "USPS",
    "DPD",
    "GLS",
    "Hermes",
    "DHL",
    "DHL Express",
    "FedEx",
)


def detect_carrier(tracking_number: str) -> str | None:
    """Return the most likely carrier name for a tracking number, if any."""
    candidate = tracking_number.strip()
    for carrier in _DETECTION_ORDER:
        pattern = CARRIER_PATTERNS[carrier]
        if pattern.fullmatch(candidate):
            return carrier
    return None


def find_tracking_numbers(text: str) -> dict[str, str]:
    """Scan free text for tracking numbers, keyed by tracking number.

    Returns a mapping of ``tracking_number -> carrier`` for every match found,
    checked in the same specificity order as :func:`detect_carrier`.
    """
    found: dict[str, str] = {}
    for carrier in _DETECTION_ORDER:
        pattern = CARRIER_PATTERNS[carrier]
        for match in pattern.finditer(text):
            number = match.group(1)
            found.setdefault(number, carrier)
    return found
