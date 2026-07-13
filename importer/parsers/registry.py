"""Auto-discovering registry of :class:`MerchantParser` plugins.

Every module in ``importer.parsers`` (other than the private ``_``-prefixed
helpers and ``base``/``registry`` themselves) is imported once; any
``MerchantParser`` subclass it defines is registered automatically. Adding
support for a new merchant is exactly one new file - nothing here, or
anywhere else in the core system, needs to change.
"""

from __future__ import annotations

import importlib
import pkgutil
from functools import lru_cache

import importer.parsers as parsers_package
from importer.emails import RawEmail
from importer.parsers.base import MerchantParser, ParsedOrder


@lru_cache
def _discover_parser_classes() -> tuple[type[MerchantParser], ...]:
    discovered: list[type[MerchantParser]] = []

    for module_info in pkgutil.iter_modules(parsers_package.__path__):
        module_name = module_info.name
        if module_name.startswith("_") or module_name in {"base", "registry"}:
            continue

        module = importlib.import_module(f"importer.parsers.{module_name}")
        for attr in vars(module).values():
            if (
                isinstance(attr, type)
                and issubclass(attr, MerchantParser)
                and attr is not MerchantParser
                and attr.__module__ == module.__name__
            ):
                discovered.append(attr)

    return tuple(discovered)


def get_parsers() -> list[MerchantParser]:
    """Return one instance of every registered merchant parser."""
    return [cls() for cls in _discover_parser_classes()]


def detect(email: RawEmail) -> ParsedOrder | None:
    """Run every registered parser against ``email``, returning the first match."""
    for parser in get_parsers():
        if parser.matches(email):
            return parser.parse(email)
    return None
