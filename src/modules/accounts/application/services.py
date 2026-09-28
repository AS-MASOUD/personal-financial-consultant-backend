import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.exceptions import EntityNotFoundException
from src.app.database.models import AccountModel
from src.modules.accounts.application.dtos import AccountCreate, AccountUpdate


class AccountService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_accounts(
        self, user_id: uuid.UUID, active_only: bool = False
    ) -> list[AccountModel]:
        stmt = select(AccountModel).where(AccountModel.user_id == user_id)
        if active_only:
            stmt = stmt.where(AccountModel.is_active == True)  # noqa: E712
        stmt = stmt.order_by(AccountModel.name)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_account(self, account_id: uuid.UUID, user_id: uuid.UUID) -> AccountModel:
        stmt = select(AccountModel).where(
            AccountModel.id == account_id,
            AccountModel.user_id == user_id,
        )
        result = await self.db.execute(stmt)
        account = result.scalar_one_or_none()
        if not account:
            raise EntityNotFoundException("Account", account_id)
        return account

    async def create_account(self, payload: AccountCreate, user_id: uuid.UUID) -> AccountModel:
        account = AccountModel(
            user_id=user_id,
            name=payload.name,
            account_type=payload.account_type,
            institution=payload.institution,
            currency=payload.currency.value,
            current_balance=payload.initial_balance,
            account_number_mask=payload.account_number_mask,
            is_active=True,
        )
        self.db.add(account)
        await self.db.flush()
        await self.db.refresh(account)
        return account

    async def update_account(
        self, account_id: uuid.UUID, payload: AccountUpdate, user_id: uuid.UUID
    ) -> AccountModel:
        account = await self.get_account(account_id, user_id)
        update_data = payload.model_dump(exclude_unset=True)
        if "currency" in update_data and update_data["currency"]:
            update_data["currency"] = update_data["currency"].value
        for field, value in update_data.items():
            setattr(account, field, value)
        await self.db.flush()
        await self.db.refresh(account)
        return account

    async def delete_account(self, account_id: uuid.UUID, user_id: uuid.UUID) -> None:
        account = await self.get_account(account_id, user_id)
        await self.db.delete(account)
        await self.db.flush()
