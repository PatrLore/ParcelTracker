"""Best-effort mapping from a provider's free-text/short status vocabulary
to the normalized status strings the rest of the application expects
(matching ``app.models.enums.ShipmentStatus`` values on the backend side,
without this package depending on the backend).
"""

from __future__ import annotations

_KEYWORDS: tuple[tuple[str, str], ...] = (
    ("out for delivery", "out_for_delivery"),
    ("delivered", "delivered"),
    ("failed", "exception"),
    ("exception", "exception"),
    ("undelivered", "exception"),
    ("returned", "returned"),
    ("return to sender", "returned"),
    ("pickup", "label_created"),
    ("info received", "label_created"),
    ("label created", "label_created"),
)


def infer_status_from_text(text: str | None) -> str:
    """Guess a normalized status from free-text event descriptions.

    Used by providers (like 17TRACK) whose per-event payload doesn't carry a
    clean status enum, only a human-readable description.
    """
    if not text:
        return "in_transit"
    lowered = text.lower()
    for keyword, status in _KEYWORDS:
        if keyword in lowered:
            return status
    return "in_transit"
