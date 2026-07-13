"""Aggregates all v1 endpoint routers under a single ``/api/v1`` prefix."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints import auth, carriers, dashboard, orders, shipments, users

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(orders.router)
api_router.include_router(shipments.router)
api_router.include_router(carriers.router)
api_router.include_router(dashboard.router)
