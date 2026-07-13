"""Refreshes shipment tracking status via the configured TrackingProvider.

The only backend module that imports from ``tracking.providers`` - the rest
of the backend only ever sees :class:`~app.models.shipment.Shipment` rows.
"""

from __future__ import annotations

from datetime import UTC, datetime

import httpx
from notification import NotificationDispatcher, NotificationMessage
from sqlalchemy.orm import Session
from tracking.provider import TrackingProvider

from app.core.logging import get_logger
from app.models.enums import ShipmentStatus
from app.models.shipment import Shipment, TrackingEvent
from app.repositories.shipment_repository import ShipmentRepository

logger = get_logger(__name__)

#: Status transitions worth interrupting someone about.
_NOTIFY_ON_STATUSES = (ShipmentStatus.DELIVERED, ShipmentStatus.DELAYED)


class TrackingSyncService:
    def __init__(
        self,
        db: Session,
        provider: TrackingProvider,
        dispatcher: NotificationDispatcher | None = None,
    ) -> None:
        self.db = db
        self.provider = provider
        self._dispatcher = dispatcher
        self.shipments = ShipmentRepository(db)

    def sync_shipment(self, shipment: Shipment) -> Shipment:
        previous_status = shipment.tracking_status

        if not shipment.tracking_registered:
            carrier_hint = shipment.carrier.name if shipment.carrier else None
            self.provider.register(shipment.tracking_number, carrier_hint=carrier_hint)
            shipment.tracking_registered = True

        events = self.provider.update(shipment.tracking_number)
        # Normalized to naive UTC: SQLite drops tzinfo on round-trip while
        # Postgres/MariaDB keep it, so comparing raw occurred_at values for
        # dedup would behave differently per backend. Naive UTC everywhere
        # keeps this dedup logic and equality checks portable.
        known = {(e.status, _to_naive_utc(e.occurred_at)) for e in shipment.tracking_events}

        for event in sorted(events, key=lambda e: e.occurred_at):
            status = _map_status(event.status)
            occurred_at = _to_naive_utc(event.occurred_at)
            key = (status, occurred_at)
            if key in known:
                continue
            known.add(key)

            shipment.tracking_events.append(
                TrackingEvent(
                    status=status,
                    description=event.description,
                    location=event.location,
                    occurred_at=occurred_at,
                )
            )
            shipment.tracking_status = status
            if status == ShipmentStatus.DELIVERED:
                shipment.delivery_date = occurred_at.date()

        if events:
            shipment.last_update = max(_to_naive_utc(event.occurred_at) for event in events)

        if (
            self._dispatcher is not None
            and shipment.tracking_status != previous_status
            and shipment.tracking_status in _NOTIFY_ON_STATUSES
        ):
            self._dispatcher.dispatch(_status_change_message(shipment))

        self.shipments.commit()
        self.db.refresh(shipment)
        return shipment

    def sync_due_shipments(self) -> int:
        """Sync every non-terminal shipment once. Returns how many were synced.

        One shipment's provider request failing doesn't stop the rest -
        a single rate-limited or momentarily-unreachable lookup shouldn't
        block refreshing every other shipment in the same pass.
        """
        synced = 0
        for shipment in self.shipments.list_non_terminal():
            try:
                self.sync_shipment(shipment)
            except httpx.HTTPError:
                logger.exception(
                    "Failed to sync tracking for shipment %s", shipment.tracking_number
                )
                continue
            synced += 1
        return synced


def _status_change_message(shipment: Shipment) -> NotificationMessage:
    if shipment.tracking_status == ShipmentStatus.DELIVERED:
        title = "Parcel delivered"
        body = f"Your parcel ({shipment.tracking_number}) has been delivered."
    else:
        title = "Parcel delayed"
        body = f"Your parcel ({shipment.tracking_number}) appears to be delayed."
    return NotificationMessage(
        event=f"shipment_{shipment.tracking_status.value}",
        title=title,
        body=body,
        metadata={
            "tracking_number": shipment.tracking_number,
            "carrier": shipment.carrier.name if shipment.carrier else "",
        },
    )


def _map_status(raw_status: str) -> ShipmentStatus:
    """Map a provider's normalized status string onto our enum.

    Falls back to IN_TRANSIT for anything unrecognized, rather than raising -
    a provider returning an unexpected value shouldn't break the sync loop.
    """
    try:
        return ShipmentStatus(raw_status)
    except ValueError:
        return ShipmentStatus.IN_TRANSIT


def _to_naive_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone(UTC).replace(tzinfo=None)
