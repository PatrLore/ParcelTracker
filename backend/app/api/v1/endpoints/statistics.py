"""Statistics endpoint (Phase 5)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.statistics import StatisticsSummary
from app.services.statistics_service import StatisticsService

router = APIRouter(
    prefix="/statistics", tags=["statistics"], dependencies=[Depends(get_current_user)]
)


@router.get("/summary", response_model=StatisticsSummary)
def get_summary(
    months: int = 12,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StatisticsSummary:
    return StatisticsService(db).get_summary(current_user.id, months=months)
