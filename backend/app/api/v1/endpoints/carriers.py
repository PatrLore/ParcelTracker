"""Carrier reference-data endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.schemas.carrier import CarrierCreate, CarrierRead
from app.services.carrier_service import CarrierService
from app.services.exceptions import AlreadyExistsError, NotFoundError

router = APIRouter(prefix="/carriers", tags=["carriers"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[CarrierRead])
def list_carriers(db: Session = Depends(get_db)) -> list[CarrierRead]:
    return CarrierService(db).list_carriers()


@router.post("", response_model=CarrierRead, status_code=status.HTTP_201_CREATED)
def create_carrier(payload: CarrierCreate, db: Session = Depends(get_db)) -> CarrierRead:
    try:
        return CarrierService(db).create_carrier(payload)
    except AlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("/{carrier_id}", response_model=CarrierRead)
def get_carrier(carrier_id: int, db: Session = Depends(get_db)) -> CarrierRead:
    try:
        return CarrierService(db).get_carrier(carrier_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
