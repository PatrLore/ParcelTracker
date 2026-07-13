"""Shared regex-extraction helpers reused by individual merchant parsers.

Kept separate from ``base.py`` so it's opt-in: a parser with unusual email
formatting can ignore these helpers entirely without breaking the plugin
interface.
"""

from __future__ import annotations

import re

from tracking import find_tracking_numbers

_AMOUNT_PATTERN = re.compile(
    r"(?P<amount>\d{1,3}(?:[.,]\d{3})*[.,]\d{2})\s*(?P<currency>EUR|USD|GBP|€|\$|£)"
    r"|(?P<currency2>EUR|USD|GBP|€|\$|£)\s*(?P<amount2>\d{1,3}(?:[.,]\d{3})*[.,]\d{2})"
)

_CURRENCY_SYMBOLS = {"€": "EUR", "$": "USD", "£": "GBP"}

#: Fallback order-number patterns (German + English) tried after any
#: merchant-specific patterns have failed to match.
GENERIC_ORDER_NUMBER_PATTERNS = [
    r"Bestellnummer[:\s]+([A-Za-z0-9\-]{5,30})",
    r"Bestell-?Nr\.?[:\s]+([A-Za-z0-9\-]{5,30})",
    r"Order (?:Number|No\.?|#)[:\s]+([A-Za-z0-9\-]{5,30})",
    r"Order[- ]ID[:\s]+([A-Za-z0-9\-]{5,30})",
]


def extract_first_match(text: str, patterns: list[str]) -> str | None:
    """Try each regex in order, returning the first capture group matched."""
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def extract_amount(text: str) -> tuple[str, str] | None:
    """Find the first monetary amount, returning ``(amount, currency)``."""
    match = _AMOUNT_PATTERN.search(text)
    if not match:
        return None

    amount = match.group("amount") or match.group("amount2")
    currency = match.group("currency") or match.group("currency2")
    return amount, _CURRENCY_SYMBOLS.get(currency, currency)


def extract_tracking_numbers(text: str) -> list[tuple[str, str]]:
    """Find tracking numbers in free text, returning ``(number, carrier)`` pairs."""
    return list(find_tracking_numbers(text).items())
