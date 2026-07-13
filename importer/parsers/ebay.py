"""eBay order/shipping confirmation parser."""

from __future__ import annotations

from importer.parsers._regex_parser import RegexMerchantParser


class EbayParser(RegexMerchantParser):
    name = "eBay"
    sender_domains = ("ebay.de", "ebay.com", "ebay.co.uk")
    order_number_patterns = [
        r"Bestellnummer[:\s]+(\d{2}-\d{5}-\d{5})",
        r"Order number[:\s]+(\d{2}-\d{5}-\d{5})",
    ]
