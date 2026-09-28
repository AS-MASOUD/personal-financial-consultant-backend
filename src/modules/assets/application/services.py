import uuid
from datetime import UTC, datetime
from decimal import ROUND_HALF_EVEN, Decimal

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.app.core.exceptions import EntityConflictException, EntityNotFoundException
from src.app.database.models import AccountModel, AssetModel, AssetPositionModel
from src.modules.assets.application.dtos import (
    AssetCreate,
    AssetPositionResponse,
    AssetPositionUpdate,
    AssetUpdate,
)


class AssetService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_assets(
        self, asset_class: str | None = None, is_active: bool | None = None
    ) -> list[AssetModel]:
        stmt = select(AssetModel)
        if asset_class:
            stmt = stmt.where(AssetModel.asset_class == asset_class)
        if is_active is not None:
            stmt = stmt.where(AssetModel.is_active == is_active)
        stmt = stmt.order_by(AssetModel.symbol)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_asset(self, asset_id: uuid.UUID) -> AssetModel:
        stmt = select(AssetModel).where(AssetModel.id == asset_id)
        result = await self.db.execute(stmt)
        asset = result.scalar_one_or_none()
        if not asset:
            raise EntityNotFoundException("Asset", asset_id)
        return asset

    async def create_asset(self, payload: AssetCreate) -> AssetModel:
        # Check duplicate symbol
        stmt = select(AssetModel).where(AssetModel.symbol == payload.symbol.upper())
        result = await self.db.execute(stmt)
        if result.scalar_one_or_none():
            raise EntityConflictException(f"Asset with symbol '{payload.symbol}' already exists.")

        now = datetime.now(UTC)
        asset = AssetModel(
            symbol=payload.symbol.upper(),
            name=payload.name,
            asset_class=payload.asset_class,
            currency=payload.currency.value,
            current_price=payload.initial_price,
            price_updated_at=now if payload.initial_price > Decimal("0") else None,
            is_active=payload.is_active,
            notes=payload.notes,
        )
        self.db.add(asset)
        await self.db.flush()
        await self.db.refresh(asset)
        return asset

    async def update_asset(self, asset_id: uuid.UUID, payload: AssetUpdate) -> AssetModel:
        asset = await self.get_asset(asset_id)
        update_data = payload.model_dump(exclude_unset=True)
        if "symbol" in update_data and update_data["symbol"] is not None:
            update_data["symbol"] = update_data["symbol"].upper().strip()
        if "currency" in update_data and update_data["currency"] is not None:
            update_data["currency"] = (
                update_data["currency"].value
                if hasattr(update_data["currency"], "value")
                else str(update_data["currency"])
            )
        if "current_price" in update_data and update_data["current_price"] is not None:
            asset.price_updated_at = datetime.now(UTC)
        for field, value in update_data.items():
            setattr(asset, field, value)
        await self.db.flush()
        await self.db.refresh(asset)
        return asset

    async def delete_asset(self, asset_id: uuid.UUID) -> None:
        asset = await self.get_asset(asset_id)
        await self.db.execute(
            delete(AssetPositionModel).where(AssetPositionModel.asset_id == asset_id)
        )
        await self.db.delete(asset)
        await self.db.flush()

    @staticmethod
    def _compute_position_response(pos: AssetPositionModel) -> AssetPositionResponse:
        current_price = pos.asset.current_price
        current_value = (pos.quantity * current_price).quantize(
            Decimal("0.0001"), rounding=ROUND_HALF_EVEN
        )
        total_cost = (pos.quantity * pos.average_cost_basis).quantize(
            Decimal("0.0001"), rounding=ROUND_HALF_EVEN
        )
        unrealized_pnl = (current_value - total_cost).quantize(
            Decimal("0.0001"), rounding=ROUND_HALF_EVEN
        )

        if total_cost > Decimal("0"):
            pnl_percent = ((unrealized_pnl / total_cost) * Decimal("100")).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_EVEN
            )
        else:
            pnl_percent = Decimal("0.00")

        return AssetPositionResponse(
            id=pos.id,
            account_id=pos.account_id,
            asset_id=pos.asset_id,
            quantity=pos.quantity,
            average_cost_basis=pos.average_cost_basis,
            current_price=current_price,
            current_value=current_value,
            unrealized_pnl=unrealized_pnl,
            unrealized_pnl_percent=pnl_percent,
            asset_symbol=pos.asset.symbol,
            asset_name=pos.asset.name,
            asset_class=pos.asset.asset_class,
            currency=pos.asset.currency,
        )

    async def list_positions(
        self, user_id: uuid.UUID, account_id: uuid.UUID | None = None
    ) -> list[AssetPositionResponse]:
        stmt = (
            select(AssetPositionModel)
            .join(AccountModel, AssetPositionModel.account_id == AccountModel.id)
            .options(selectinload(AssetPositionModel.asset))
            .where(AccountModel.user_id == user_id)
        )
        if account_id:
            stmt = stmt.where(AssetPositionModel.account_id == account_id)
        result = await self.db.execute(stmt)
        positions = result.scalars().all()
        return [self._compute_position_response(pos) for pos in positions]

    async def get_position(
        self, position_id: uuid.UUID, user_id: uuid.UUID
    ) -> AssetPositionModel:
        stmt = (
            select(AssetPositionModel)
            .join(AccountModel, AssetPositionModel.account_id == AccountModel.id)
            .options(selectinload(AssetPositionModel.asset))
            .where(
                AssetPositionModel.id == position_id,
                AccountModel.user_id == user_id,
            )
        )
        result = await self.db.execute(stmt)
        position = result.scalar_one_or_none()
        if not position:
            raise EntityNotFoundException("AssetPosition", position_id)
        return position

    async def update_position(
        self,
        position_id: uuid.UUID,
        payload: AssetPositionUpdate,
        user_id: uuid.UUID,
    ) -> AssetPositionResponse:
        position = await self.get_position(position_id=position_id, user_id=user_id)
        if payload.quantity is not None:
            position.quantity = payload.quantity
        if payload.average_cost_basis is not None:
            position.average_cost_basis = payload.average_cost_basis
        await self.db.flush()
        await self.db.refresh(position)
        return self._compute_position_response(position)

    async def delete_position(
        self, position_id: uuid.UUID, user_id: uuid.UUID
    ) -> None:
        position = await self.get_position(position_id=position_id, user_id=user_id)
        await self.db.delete(position)
        await self.db.flush()


