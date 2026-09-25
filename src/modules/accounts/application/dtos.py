import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from src.shared.domain.currency import Currency


class AccountBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    account_type: str = Field(
        ..., description="checking, savings, brokerage, crypto, cash, retirement"
    )
    institution: str | None = Field(None, max_length=100)
    currency: Currency = Field(default=Currency.USD)
    account_number_mask: str | None = Field(None, max_length=20)


class AccountCreate(AccountBase):
    initial_balance: Decimal = Field(default=Decimal("0.0000"), ge=0)


class AccountUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    account_type: str | None = None
    institution: str | None = None
    currency: Currency | None = None
    account_number_mask: str | None = None
    is_active: bool | None = None


class AccountResponse(AccountBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    current_balance: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime
