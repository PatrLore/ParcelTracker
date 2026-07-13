"""Order endpoints. All orders are scoped to the authenticated user."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.order import OrderCreate, OrderRead, OrderUpdate
from app.services.exceptions import NotFoundError
from app.services.order_service import OrderService

router = APIRouter(prefix="/orders", tags=["orders"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[OrderRead])
def list_orders(
    offset: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[OrderRead]:
    return OrderService(db).list_orders(current_user.id, offset=offset, limit=limit)


@router.post("", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
def create_order(
    payload: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OrderRead:
    return OrderService(db).create_order(payload, current_user.id)


@router.get("/{order_id}", response_model=OrderRead)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OrderRead:
    try:
        return OrderService(db).get_order(order_id, current_user.id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch("/{order_id}", response_model=OrderRead)
def update_order(
    order_id: int,
    payload: OrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OrderRead:
    try:
        return OrderService(db).update_order(order_id, payload, current_user.id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    try:
        OrderService(db).delete_order(order_id, current_user.id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
