import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from src.shared.domain.currency import Currency


class LiabilityBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    liability_type: str = Field(
        default="personal_loan",
        description="personal_loan, bank_loan, friend_borrowed, friend_lent, bnpl, mortgage, auto_loan, credit_card, other",
    )
    lender: str | None = Field(None, max_length=100, description="Bank, platform, or friend/counterparty name")
    interest_rate_percent: Decimal = Field(default=Decimal("0.000"), ge=0, le=100)
    monthly_payment: Decimal = Field(default=Decimal("0.0000"), ge=0)
    start_date: date = Field(default_factory=date.today)
    maturity_date: date | None = None
    currency: Currency = Field(default=Currency.TOMAN)


class LiabilityCreate(LiabilityBase):
    original_principal: Decimal = Field(..., gt=0)
    current_balance: Decimal | None = None
    term_months: int | None = Field(default=None, ge=1, le=600)


class LiabilityUpdate(BaseModel):
    name: str | None = None
    liability_type: str | None = None
    lender: str | None = None
    original_principal: Decimal | None = None
    current_balance: Decimal | None = None
    interest_rate_percent: Decimal | None = None
    monthly_payment: Decimal | None = None
    start_date: date | None = None
    maturity_date: date | None = None
    currency: Currency | None = None



class LiabilityPaymentCreate(BaseModel):
    liability_id: uuid.UUID
    payment_date: date
    principal_amount: Decimal = Field(..., ge=0)
    interest_amount: Decimal = Field(..., ge=0)
    extra_principal: Decimal = Field(default=Decimal("0.0000"), ge=0)


class LiabilityPaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    liability_id: uuid.UUID
    payment_date: date
    principal_amount: Decimal
    interest_amount: Decimal
    extra_principal: Decimal
    total_payment: Decimal
    created_at: datetime


class LiabilityResponse(LiabilityBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    original_principal: Decimal
    current_balance: Decimal
    created_at: datetime
    updated_at: datetime
    repaid_amount: Decimal
    repaid_percent: Decimal
    type_config: "LiabilityTypeResponse | None" = None


class LiabilityTypeBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=50)
    label: str = Field(..., min_length=1, max_length=100)
    short_label: str | None = Field(None, max_length=100)
    description: str | None = None
    icon: str = Field(default="Building", max_length=50)
    default_rate: Decimal = Field(default=Decimal("0.000"), ge=0, le=100)
    default_term_months: int = Field(default=12, ge=1, le=600)
    is_friend: bool = False
    direction: str = Field(default="debt", description="debt or claim")
    display_order: int = Field(default=0)
    is_active: bool = True


class LiabilityTypeCreate(LiabilityTypeBase):
    pass


class LiabilityTypeResponse(LiabilityTypeBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

