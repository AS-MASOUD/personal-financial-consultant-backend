from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.database.models import UserModel
from src.app.database.session import get_db_session
from src.modules.analytics.application.dtos import (
    HistoricalSnapshotResponse,
    OverviewDashboardResponse,
)
from src.modules.analytics.application.services import AnalyticsService
from src.modules.auth.presentation.dependencies import get_current_user

analytics_router = APIRouter(prefix="/analytics", tags=["Analytics & Overview"])


def get_analytics_service(db: AsyncSession = Depends(get_db_session)) -> AnalyticsService:
    return AnalyticsService(db)


@analytics_router.get("/overview", response_model=OverviewDashboardResponse)
async def get_overview(
    current_user: UserModel = Depends(get_current_user),
    service: AnalyticsService = Depends(get_analytics_service),
) -> OverviewDashboardResponse:
    return await service.get_overview(current_user=current_user)


@analytics_router.get("/snapshots", response_model=list[HistoricalSnapshotResponse])
async def get_historical_snapshots(
    limit: int = Query(90, ge=1, le=365),
    current_user: UserModel = Depends(get_current_user),
    service: AnalyticsService = Depends(get_analytics_service),
) -> list[HistoricalSnapshotResponse]:
    return await service.get_historical_snapshots(limit=limit, current_user=current_user)


@analytics_router.post(
    "/snapshots/record",
    response_model=HistoricalSnapshotResponse,
    status_code=status.HTTP_201_CREATED,
)
async def record_snapshot(
    snapshot_date: date | None = None,
    current_user: UserModel = Depends(get_current_user),
    service: AnalyticsService = Depends(get_analytics_service),
) -> HistoricalSnapshotResponse:
    snap = await service.record_snapshot(snapshot_date=snapshot_date, current_user=current_user)
    return HistoricalSnapshotResponse.model_validate(snap)
