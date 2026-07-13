"""Carrier reference-data business logic."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.carrier import Carrier
from app.repositories.carrier_repository import CarrierRepository
from app.schemas.carrier import CarrierCreate
from app.services.exceptions import AlreadyExistsError, NotFoundError


class CarrierService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.carriers = CarrierRepository(db)

    def list_carriers(self) -> list[Carrier]:
        return self.carriers.list(limit=1000)

    def create_carrier(self, data: CarrierCreate) -> Carrier:
        if self.carriers.get_by_name(data.name) is not None:
            raise AlreadyExistsError(f"Carrier {data.name} already exists")
        carrier = self.carriers.add(Carrier(**data.model_dump()))
        self.carriers.commit()
        return carrier

    def get_carrier(self, carrier_id: int) -> Carrier:
        carrier = self.carriers.get(carrier_id)
        if carrier is None:
            raise NotFoundError(f"Carrier {carrier_id} not found")
        return carrier
