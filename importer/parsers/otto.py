"""Otto order/shipping confirmation parser."""

from __future__ import annotations

from importer.parsers._regex_parser import RegexMerchantParser


class OttoParser(RegexMerchantParser):
    name = "Otto"
    sender_domains = ("otto.de",)
    order_number_patterns = [
        r"Bestellnummer[:\s]+(\d{9,12})",
        r"Auftragsnummer[:\s]+(\d{9,12})",
    ]
