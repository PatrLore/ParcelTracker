"""Decathlon order/shipping confirmation parser."""

from __future__ import annotations

from importer.parsers._regex_parser import RegexMerchantParser


class DecathlonParser(RegexMerchantParser):
    name = "Decathlon"
    sender_domains = ("decathlon.de", "decathlon.com")
    order_number_patterns = [
        r"Bestellnummer[:\s]+([A-Z0-9]{9,15})",
        r"Order number[:\s]+([A-Z0-9]{9,15})",
    ]
