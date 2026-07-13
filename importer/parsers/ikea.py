"""IKEA order/shipping confirmation parser."""

from __future__ import annotations

from importer.parsers._regex_parser import RegexMerchantParser


class IkeaParser(RegexMerchantParser):
    name = "IKEA"
    sender_domains = ("ikea.de", "ikea.com")
    order_number_patterns = [
        r"Bestellnummer[:\s]+(\d{3}\.\d{3}\.\d{2})",
        r"Order number[:\s]+(\d{3}\.\d{3}\.\d{2})",
    ]
