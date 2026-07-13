"""The merchant-parser plugin interface.

Every merchant parser (``importer/parsers/amazon.py``, ``ebay.py``, ...)
subclasses :class:`MerchantParser`. Adding support for a new merchant means
adding one new module in this package - the registry
(``importer/parsers/registry.py``) discovers it automatically, with no
changes to any existing file.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date

from importer.emails import RawEmail


@dataclass(frozen=True)
class ParsedOrder:
    """Structured data extracted from a shipping-confirmation email."""

    merchant: str
    order_number: str | None = None
    order_date: date | None = None
    invoice_amount: str | None = None
    currency: str | None = None
    tracking_numbers: list[str] = field(default_factory=list)
    carrier_hint: str | None = None


class MerchantParser(ABC):
    """Detects and extracts order data for one merchant's confirmation emails."""

    #: Human-readable merchant name, used as ``ParsedOrder.merchant``.
    name: str

    @abstractmethod
    def matches(self, email: RawEmail) -> bool:
        """Whether this parser recognizes the given email as one of its own."""

    @abstractmethod
    def parse(self, email: RawEmail) -> ParsedOrder | None:
        """Extract order data. Only called after :meth:`matches` returns True."""
