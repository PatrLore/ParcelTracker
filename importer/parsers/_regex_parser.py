"""A declarative :class:`MerchantParser` base for the common case: matching
by sender domain and extracting fields via regex. Most merchant parsers only
need to declare data (domains, patterns); this base implements the shared
``matches``/``parse`` logic once.
"""

from __future__ import annotations

from importer.emails import RawEmail
from importer.parsers._extract import (
    GENERIC_ORDER_NUMBER_PATTERNS,
    extract_amount,
    extract_first_match,
    extract_tracking_numbers,
)
from importer.parsers.base import MerchantParser, ParsedOrder


class RegexMerchantParser(MerchantParser):
    """Matches by sender domain; extracts fields via regex patterns."""

    sender_domains: tuple[str, ...] = ()
    order_number_patterns: list[str] = []

    def matches(self, email: RawEmail) -> bool:
        sender = email.sender.lower()
        return any(domain in sender for domain in self.sender_domains)

    def parse(self, email: RawEmail) -> ParsedOrder | None:
        text = f"{email.subject}\n{email.body}"

        order_number = extract_first_match(
            text, [*self.order_number_patterns, *GENERIC_ORDER_NUMBER_PATTERNS]
        )
        amount_result = extract_amount(text)
        tracking = extract_tracking_numbers(text)

        return ParsedOrder(
            merchant=self.name,
            order_number=order_number,
            order_date=email.received_at.date(),
            invoice_amount=amount_result[0] if amount_result else None,
            currency=amount_result[1] if amount_result else None,
            tracking_numbers=[number for number, _carrier in tracking],
            carrier_hint=tracking[0][1] if tracking else None,
        )
