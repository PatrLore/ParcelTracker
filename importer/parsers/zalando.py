"""Zalando order/shipping confirmation parser."""

from __future__ import annotations

from importer.parsers._regex_parser import RegexMerchantParser


class ZalandoParser(RegexMerchantParser):
    name = "Zalando"
    sender_domains = ("zalando.de",)
    order_number_patterns = [
        r"Bestellnummer[:\s]+(\d{9,12})",
    ]
