"""Saturn order/shipping confirmation parser."""

from __future__ import annotations

from importer.parsers._regex_parser import RegexMerchantParser


class SaturnParser(RegexMerchantParser):
    name = "Saturn"
    sender_domains = ("saturn.de",)
    order_number_patterns = [
        r"Bestellnummer[:\s]+([A-Z0-9]{8,15})",
    ]
