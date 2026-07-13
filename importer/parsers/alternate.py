"""Alternate.de order/shipping confirmation parser."""

from __future__ import annotations

from importer.parsers._regex_parser import RegexMerchantParser


class AlternateParser(RegexMerchantParser):
    name = "Alternate"
    sender_domains = ("alternate.de",)
    order_number_patterns = [
        r"Bestellnummer[:\s]+(\d{7,10})",
    ]
