import uuid
from decimal import ROUND_HALF_EVEN, Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.exceptions import EntityNotFoundException, FinancialCalculationException
from src.app.database.models import (
    AccountModel,
    AssetModel,
    AssetPositionModel,
    TransactionModel,
    UserModel,
)
from src.modules.transactions.application.dtos import TransactionCreate


class TransactionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_transactions(
        self,
        current_user: UserModel,
        account_id: uuid.UUID | None = None,
        asset_id: uuid.UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[TransactionModel]:
        stmt = (
            select(TransactionModel)
            .join(AccountModel, TransactionModel.account_id == AccountModel.id)
            .where(AccountModel.user_id == current_user.id)
        )
        if account_id:
            stmt = stmt.where(TransactionModel.account_id == account_id)
        if asset_id:
            stmt = stmt.where(TransactionModel.asset_id == asset_id)
        stmt = stmt.order_by(TransactionModel.transaction_date.desc()).limit(limit).offset(offset)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create_transaction(
        self, payload: TransactionCreate, current_user: UserModel
    ) -> TransactionModel:
        # Validate account exists and belongs to current user
        stmt = select(AccountModel).where(
            AccountModel.id == payload.account_id,
            AccountModel.user_id == current_user.id,
        )
        result = await self.db.execute(stmt)
        account = result.scalar_one_or_none()
        if not account:
            raise EntityNotFoundException("Account", payload.account_id)

        # Asset validation if provided
        asset = None
        if payload.asset_id:
            stmt = select(AssetModel).where(AssetModel.id == payload.asset_id)
            result = await self.db.execute(stmt)
            asset = result.scalar_one_or_none()
            if not asset:
                raise EntityNotFoundException("Asset", payload.asset_id)

        t_type = payload.transaction_type.upper()

        # Update cash balance and position deterministically
        if t_type == "DEPOSIT":
            account.current_balance += payload.total_amount
        elif t_type in ("WITHDRAWAL", "FEE"):
            account.current_balance -= payload.total_amount
        elif t_type in ("DIVIDEND", "INTEREST"):
            account.current_balance += payload.total_amount
        elif t_type == "BUY":
            if not payload.asset_id or not payload.quantity:
                raise FinancialCalculationException(
                    "BUY transactions require an asset_id and quantity."
                )
            cost = payload.total_amount + payload.fee
            account.current_balance -= cost

            # Find or create position
            pos_stmt = select(AssetPositionModel).where(
                AssetPositionModel.account_id == payload.account_id,
                AssetPositionModel.asset_id == payload.asset_id,
            )
            pos_result = await self.db.execute(pos_stmt)
            position = pos_result.scalar_one_or_none()

            if position:
                # Weighted average cost basis calculation
                old_total_cost = position.quantity * position.average_cost_basis
                new_quantity = position.quantity + payload.quantity
                if new_quantity > Decimal("0"):
                    new_avg_cost = (old_total_cost + payload.total_amount) / new_quantity
                    position.average_cost_basis = new_avg_cost.quantize(
                        Decimal("0.0001"), rounding=ROUND_HALF_EVEN
                    )
                position.quantity = new_quantity
            else:
                unit_cost = (payload.total_amount / payload.quantity).quantize(
                    Decimal("0.0001"), rounding=ROUND_HALF_EVEN
                )
                position = AssetPositionModel(
                    account_id=payload.account_id,
                    asset_id=payload.asset_id,
                    quantity=payload.quantity,
                    average_cost_basis=unit_cost,
                )
                self.db.add(position)

        elif t_type == "SELL":
            if not payload.asset_id or not payload.quantity:
                raise FinancialCalculationException(
                    "SELL transactions require an asset_id and quantity."
                )
            net_proceeds = payload.total_amount - payload.fee
            account.current_balance += net_proceeds

            pos_stmt = select(AssetPositionModel).where(
                AssetPositionModel.account_id == payload.account_id,
                AssetPositionModel.asset_id == payload.asset_id,
            )
            pos_result = await self.db.execute(pos_stmt)
            position = pos_result.scalar_one_or_none()
            if not position or position.quantity < payload.quantity:
                raise FinancialCalculationException(
                    "Insufficient asset quantity for SELL transaction."
                )

            position.quantity -= payload.quantity

        transaction = TransactionModel(
            account_id=payload.account_id,
            asset_id=payload.asset_id,
            transaction_type=t_type,
            transaction_date=payload.transaction_date,
            quantity=payload.quantity,
            unit_price=payload.unit_price,
            total_amount=payload.total_amount,
            fee=payload.fee,
            currency=payload.currency.value,
            notes=payload.notes,
            is_reconciled=True,
        )
        self.db.add(transaction)
        await self.db.flush()
        await self.db.refresh(transaction)
        return transaction
