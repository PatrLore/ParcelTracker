"""AliExpress order/shipping confirmation parser."""

from __future__ import annotations

from importer.parsers._regex_parser import RegexMerchantParser


class AliExpressParser(RegexMerchantParser):
    name = "AliExpress"
    sender_domains = ("aliexpress.com",)
    order_number_patterns = [
        r"Order number[:\s]+(\d{18,20})",
        r"Order ID[:\s]+(\d{18,20})",
    ]
