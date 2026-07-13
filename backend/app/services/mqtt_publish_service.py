"""Publishes aggregate parcel counts to MQTT as Home Assistant Discovery
sensors (Phase 4).

Counts are global (across every user), matching the single-household
deployment the spec's MQTT sensors are designed for - one Home Assistant
instance driving one set of `parcel.*` sensors, not one set per user.
"""

from __future__ import annotations

from datetime import date

from mqtt.publisher import MqttPublisher
from sqlalchemy.orm import Session

from app.models.enums import ShipmentStatus
from app.repositories.shipment_repository import ShipmentRepository


class MqttPublishService:
    def __init__(self, db: Session, publisher: MqttPublisher) -> None:
        self.db = db
        self.publisher = publisher
        self.shipments = ShipmentRepository(db)

    def publish(self) -> None:
        values: dict[str, str | int] = {
            "total": self.shipments.count_all(),
            "in_transit": (
                self.shipments.count_all_by_status(ShipmentStatus.IN_TRANSIT)
                + self.shipments.count_all_by_status(ShipmentStatus.OUT_FOR_DELIVERY)
            ),
            "delivered_today": self.shipments.count_all_delivered_on(date.today()),
            "delayed": self.shipments.count_all_by_status(ShipmentStatus.DELAYED),
        }

        next_delivery = self.shipments.next_delivery_date()
        if next_delivery is not None:
            values["next_delivery"] = next_delivery.isoformat()

        self.publisher.connect()
        try:
            self.publisher.publish_discovery()
            self.publisher.publish_state(values)
        finally:
            self.publisher.disconnect()
