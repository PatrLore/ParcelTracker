"""Shipment and tracking-history business logic.

Status updates are expected to originate from a :class:`TrackingProvider`
implementation (see ``tracking/``) in a later phase; for now they can also be
applied directly through the API for manual tracking.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.shipment import Shipment, TrackingEvent
from app.repositories.shipment_repository import ShipmentRepository
from app.schemas.shipment import ShipmentCreate, ShipmentUpdate
from app.services.exceptions import NotFoundError


class ShipmentService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.shipments = ShipmentRepository(db)

    def list_shipments(self, user_id: int, offset: int = 0, limit: int = 100) -> list[Shipment]:
        return self.shipments.list_for_user(user_id, offset=offset, limit=limit)

    def get_shipment(self, shipment_id: int, user_id: int) -> Shipment:
        shipment = self.shipments.get_for_user(shipment_id, user_id)
        if shipment is None:
            raise NotFoundError(f"Shipment {shipment_id} not found")
        return shipment

    def create_shipment(self, data: ShipmentCreate) -> Shipment:
        shipment = Shipment(**data.model_dump())
        shipment = self.shipments.add(shipment)
        self.shipments.commit()
        return shipment

    def update_status(self, shipment_id: int, user_id: int, data: ShipmentUpdate) -> Shipment:
        shipment = self.get_shipment(shipment_id, user_id)
        changes = data.model_dump(exclude_unset=True)
        for field, value in changes.items():
            setattr(shipment, field, value)
        if "tracking_status" in changes:
            shipment.last_update = datetime.now(UTC)
            shipment.tracking_events.append(
                TrackingEvent(
                    status=shipment.tracking_status,
                    occurred_at=shipment.last_update,
                )
            )
        self.shipments.commit()
        self.db.refresh(shipment)
        return shipment
