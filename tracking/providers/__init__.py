"""Concrete :class:`~tracking.provider.TrackingProvider` implementations.

Each provider talks to one external tracking-aggregator API. Response field
names are based on each provider's public REST API documentation at the
time of writing; if a provider changes its schema, only that provider's
module needs updating - the rest of the application depends solely on
:class:`~tracking.provider.TrackingProvider`.
"""

from tracking.providers.factory import create_provider

__all__ = ["create_provider"]
