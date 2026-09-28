import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from src.shared.domain.currency import Currency


class TransactionCreate(BaseModel):
    account_id: uuid.UUID
    asset_id: uuid.UUID | None = None
    transaction_type: str = Field(
        ..., description="BUY, SELL, DEPOSIT, WITHDRAWAL, DIVIDEND, INTEREST, FEE, TRANSFER"
    )
    transaction_date: datetime
    quantity: Decimal | None = Field(None, ge=0)
    unit_price: Decimal | None = Field(None, ge=0)
    total_amount: Decimal = Field(..., ge=0)
    fee: Decimal = Field(default=Decimal("0.0000"), ge=0)
    currency: Currency = Field(default=Currency.TOMAN)
    notes: str | None = None


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    account_id: uuid.UUID
    asset_id: uuid.UUID | None
    transaction_type: str
    transaction_date: datetime
    quantity: Decimal | None
    unit_price: Decimal | None
    total_amount: Decimal
    fee: Decimal
    currency: str
    notes: str | None
    is_reconciled: bool
    created_at: datetime
    updated_at: datetime
