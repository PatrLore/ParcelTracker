"""Domain-level exceptions raised by the service layer.

API routes translate these into the appropriate HTTP responses, keeping
HTTP concerns out of the business logic.
"""

from __future__ import annotations


class ServiceError(Exception):
    """Base class for all service-layer errors."""


class NotFoundError(ServiceError):
    """Raised when a requested entity does not exist."""


class AlreadyExistsError(ServiceError):
    """Raised when attempting to create a duplicate entity."""


class InvalidCredentialsError(ServiceError):
    """Raised when authentication fails."""
