"""Amazon order/shipping confirmation parser."""

from __future__ import annotations

from importer.parsers._regex_parser import RegexMerchantParser


class AmazonParser(RegexMerchantParser):
    name = "Amazon"
    sender_domains = ("amazon.de", "amazon.com", "marketplace.amazon.de", "amazon.co.uk")
    order_number_patterns = [
        r"Bestellnummer[:\s]+(\d{3}-\d{7}-\d{7})",
        r"Order #[:\s]*(\d{3}-\d{7}-\d{7})",
        r"(\d{3}-\d{7}-\d{7})",
    ]
