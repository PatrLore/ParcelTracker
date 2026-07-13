"""Shipment endpoints. All shipments are scoped to the authenticated user."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.shipment import ShipmentCreate, ShipmentRead, ShipmentUpdate
from app.services.exceptions import NotFoundError
from app.services.shipment_service import ShipmentService

router = APIRouter(
    prefix="/shipments", tags=["shipments"], dependencies=[Depends(get_current_user)]
)


@router.get("", response_model=list[ShipmentRead])
def list_shipments(
    offset: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ShipmentRead]:
    return ShipmentService(db).list_shipments(current_user.id, offset=offset, limit=limit)


@router.post("", response_model=ShipmentRead, status_code=status.HTTP_201_CREATED)
def create_shipment(payload: ShipmentCreate, db: Session = Depends(get_db)) -> ShipmentRead:
    return ShipmentService(db).create_shipment(payload)


@router.get("/{shipment_id}", response_model=ShipmentRead)
def get_shipment(
    shipment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ShipmentRead:
    try:
        return ShipmentService(db).get_shipment(shipment_id, current_user.id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch("/{shipment_id}", response_model=ShipmentRead)
def update_shipment(
    shipment_id: int,
    payload: ShipmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ShipmentRead:
    try:
        return ShipmentService(db).update_status(shipment_id, current_user.id, payload)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
