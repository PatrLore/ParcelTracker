"""Kaufland.de order/shipping confirmation parser."""

from __future__ import annotations

from importer.parsers._regex_parser import RegexMerchantParser


class KauflandParser(RegexMerchantParser):
    name = "Kaufland"
    sender_domains = ("kaufland.de",)
    order_number_patterns = [
        r"Bestellnummer[:\s]+([A-Z0-9\-]{10,20})",
    ]
