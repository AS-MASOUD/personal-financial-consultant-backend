import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.database.models import UserModel
from src.app.database.session import get_db_session
from src.modules.auth.presentation.dependencies import get_current_user
from src.modules.transactions.application.dtos import TransactionCreate, TransactionResponse
from src.modules.transactions.application.services import TransactionService

transactions_router = APIRouter(prefix="/transactions", tags=["Transactions"])


def get_transaction_service(db: AsyncSession = Depends(get_db_session)) -> TransactionService:
    return TransactionService(db)


@transactions_router.get("", response_model=list[TransactionResponse])
async def list_transactions(
    account_id: uuid.UUID | None = None,
    asset_id: uuid.UUID | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: UserModel = Depends(get_current_user),
    service: TransactionService = Depends(get_transaction_service),
) -> list[TransactionResponse]:
    txs = await service.list_transactions(
        current_user=current_user,
        account_id=account_id,
        asset_id=asset_id,
        limit=limit,
        offset=offset,
    )
    return [TransactionResponse.model_validate(t) for t in txs]


@transactions_router.post(
    "", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED
)
async def create_transaction(
    payload: TransactionCreate,
    current_user: UserModel = Depends(get_current_user),
    service: TransactionService = Depends(get_transaction_service),
) -> TransactionResponse:
    tx = await service.create_transaction(payload, current_user=current_user)
    return TransactionResponse.model_validate(tx)
