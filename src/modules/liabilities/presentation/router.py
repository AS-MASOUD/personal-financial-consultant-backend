from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.database.models import UserModel
from src.app.database.session import get_db_session
from src.modules.auth.presentation.dependencies import get_current_user
from src.modules.liabilities.application.dtos import (
    LiabilityCreate,
    LiabilityPaymentCreate,
    LiabilityPaymentResponse,
    LiabilityResponse,
)
from src.modules.liabilities.application.services import LiabilityService

liabilities_router = APIRouter(prefix="/liabilities", tags=["Liabilities"])


def get_liability_service(db: AsyncSession = Depends(get_db_session)) -> LiabilityService:
    return LiabilityService(db)


@liabilities_router.get("", response_model=list[LiabilityResponse])
async def list_liabilities(
    current_user: UserModel = Depends(get_current_user),
    service: LiabilityService = Depends(get_liability_service),
) -> list[LiabilityResponse]:
    return await service.list_liabilities(current_user=current_user)


@liabilities_router.post("", status_code=status.HTTP_201_CREATED)
async def create_liability(
    payload: LiabilityCreate,
    current_user: UserModel = Depends(get_current_user),
    service: LiabilityService = Depends(get_liability_service),
):
    return await service.create_liability(payload, current_user=current_user)


@liabilities_router.post(
    "/payments", response_model=LiabilityPaymentResponse, status_code=status.HTTP_201_CREATED
)
async def record_payment(
    payload: LiabilityPaymentCreate,
    current_user: UserModel = Depends(get_current_user),
    service: LiabilityService = Depends(get_liability_service),
) -> LiabilityPaymentResponse:
    payment = await service.record_payment(payload, current_user=current_user)
    return LiabilityPaymentResponse.model_validate(payment)


@liabilities_router.get("/calculate-schedule")
async def calculate_amortization_schedule(
    principal: Decimal = Query(..., gt=0),
    interest_rate: Decimal = Query(..., ge=0),
    term_months: int = Query(..., gt=0),
) -> list[dict[str, Any]]:
    return LiabilityService.calculate_amortization_schedule(
        principal=principal,
        annual_rate_percent=interest_rate,
        term_months=term_months,
    )
