"""MediaMarkt order/shipping confirmation parser."""

from __future__ import annotations

from importer.parsers._regex_parser import RegexMerchantParser


class MediaMarktParser(RegexMerchantParser):
    name = "MediaMarkt"
    sender_domains = ("mediamarkt.de",)
    order_number_patterns = [
        r"Bestellnummer[:\s]+([A-Z0-9]{8,15})",
    ]
