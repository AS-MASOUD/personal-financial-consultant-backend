import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.database.session import get_db_session
from src.modules.cashflow.application.dtos import (
    CashflowEntryCreate,
    CashflowEntryResponse,
    CashflowSummary,
    CategoryCreate,
    CategoryResponse,
)
from src.modules.cashflow.application.services import CashflowService

cashflow_router = APIRouter(prefix="/cashflow", tags=["Cash Flow"])


def get_cashflow_service(db: AsyncSession = Depends(get_db_session)) -> CashflowService:
    return CashflowService(db)


@cashflow_router.get("/categories", response_model=list[CategoryResponse])
async def list_categories(
    flow_type: str | None = None,
    service: CashflowService = Depends(get_cashflow_service),
) -> list[CategoryResponse]:
    categories = await service.list_categories(flow_type=flow_type)
    return [CategoryResponse.model_validate(c) for c in categories]


@cashflow_router.post(
    "/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED
)
async def create_category(
    payload: CategoryCreate,
    service: CashflowService = Depends(get_cashflow_service),
) -> CategoryResponse:
    category = await service.create_category(payload)
    return CategoryResponse.model_validate(category)


@cashflow_router.get("/entries", response_model=list[CashflowEntryResponse])
async def list_entries(
    start_date: date | None = None,
    end_date: date | None = None,
    category_id: uuid.UUID | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    service: CashflowService = Depends(get_cashflow_service),
) -> list[CashflowEntryResponse]:
    return await service.list_entries(
        start_date=start_date,
        end_date=end_date,
        category_id=category_id,
        limit=limit,
        offset=offset,
    )


@cashflow_router.post("/entries", status_code=status.HTTP_201_CREATED)
async def create_entry(
    payload: CashflowEntryCreate,
    service: CashflowService = Depends(get_cashflow_service),
):
    return await service.create_entry(payload)


@cashflow_router.get("/summary", response_model=CashflowSummary)
async def get_summary(
    start_date: date | None = None,
    end_date: date | None = None,
    service: CashflowService = Depends(get_cashflow_service),
) -> CashflowSummary:
    return await service.get_summary(start_date=start_date, end_date=end_date)
