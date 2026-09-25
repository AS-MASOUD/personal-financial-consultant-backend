import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from src.shared.domain.currency import Currency


class AssetBase(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=30)
    name: str = Field(..., min_length=1, max_length=150)
    asset_class: str = Field(
        ..., description="equity, fixed_income, commodity, real_estate, crypto, cash"
    )
    currency: Currency = Field(default=Currency.USD)
    notes: str | None = None


class AssetCreate(AssetBase):
    initial_price: Decimal = Field(default=Decimal("0.0000"), ge=0)


class AssetUpdate(BaseModel):
    name: str | None = None
    asset_class: str | None = None
    current_price: Decimal | None = Field(None, ge=0)
    notes: str | None = None


class AssetResponse(AssetBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    current_price: Decimal
    price_updated_at: datetime | None
    created_at: datetime
    updated_at: datetime


class AssetPositionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    account_id: uuid.UUID
    asset_id: uuid.UUID
    quantity: Decimal
    average_cost_basis: Decimal
    current_price: Decimal
    current_value: Decimal
    unrealized_pnl: Decimal
    unrealized_pnl_percent: Decimal
    asset_symbol: str
    asset_name: str
    asset_class: str
    currency: str
