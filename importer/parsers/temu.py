"""Temu order/shipping confirmation parser."""

from __future__ import annotations

from importer.parsers._regex_parser import RegexMerchantParser


class TemuParser(RegexMerchantParser):
    name = "Temu"
    sender_domains = ("temu.com",)
    order_number_patterns = [
        r"Order ID[:\s]+(PO-\d{15,20})",
        r"Order number[:\s]+(PO-\d{15,20})",
    ]
