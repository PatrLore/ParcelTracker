"""System/version endpoints."""

from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.schemas.system import VersionInfo
from app.services.version_service import get_version_info

router = APIRouter(prefix="/system", tags=["system"], dependencies=[Depends(get_current_user)])


@router.get("/version", response_model=VersionInfo)
def get_version() -> VersionInfo:
    with httpx.Client(timeout=5.0) as client:
        return get_version_info(client)
