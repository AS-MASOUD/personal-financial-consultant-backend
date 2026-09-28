import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.database.models import UserModel
from src.app.database.session import get_db_session
from src.modules.accounts.application.dtos import AccountCreate, AccountResponse, AccountUpdate
from src.modules.accounts.application.services import AccountService
from src.modules.auth.presentation.dependencies import get_current_user

accounts_router = APIRouter(prefix="/accounts", tags=["Accounts"])


def get_account_service(db: AsyncSession = Depends(get_db_session)) -> AccountService:
    return AccountService(db)


@accounts_router.get("", response_model=list[AccountResponse])
async def list_accounts(
    active_only: bool = False,
    service: AccountService = Depends(get_account_service),
    current_user: UserModel = Depends(get_current_user),
) -> list[AccountResponse]:
    accounts = await service.list_accounts(user_id=current_user.id, active_only=active_only)
    return [AccountResponse.model_validate(a) for a in accounts]


@accounts_router.get("/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: uuid.UUID,
    service: AccountService = Depends(get_account_service),
    current_user: UserModel = Depends(get_current_user),
) -> AccountResponse:
    account = await service.get_account(account_id, user_id=current_user.id)
    return AccountResponse.model_validate(account)


@accounts_router.post("", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    payload: AccountCreate,
    service: AccountService = Depends(get_account_service),
    current_user: UserModel = Depends(get_current_user),
) -> AccountResponse:
    account = await service.create_account(payload, user_id=current_user.id)
    return AccountResponse.model_validate(account)


@accounts_router.patch("/{account_id}", response_model=AccountResponse)
async def update_account(
    account_id: uuid.UUID,
    payload: AccountUpdate,
    service: AccountService = Depends(get_account_service),
    current_user: UserModel = Depends(get_current_user),
) -> AccountResponse:
    account = await service.update_account(account_id, payload, user_id=current_user.id)
    return AccountResponse.model_validate(account)


@accounts_router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    account_id: uuid.UUID,
    service: AccountService = Depends(get_account_service),
    current_user: UserModel = Depends(get_current_user),
) -> None:
    await service.delete_account(account_id, user_id=current_user.id)
