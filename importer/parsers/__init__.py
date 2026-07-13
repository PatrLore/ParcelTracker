"""Pluggable merchant email parsers.

Drop a new module in this package (subclassing
:class:`~importer.parsers.base.MerchantParser`, typically via the
:class:`~importer.parsers._regex_parser.RegexMerchantParser` convenience
base) to support a new merchant - :func:`registry.detect` picks it up
automatically.
"""

from importer.parsers.base import MerchantParser, ParsedOrder
from importer.parsers.registry import detect, get_parsers

__all__ = ["MerchantParser", "ParsedOrder", "detect", "get_parsers"]
