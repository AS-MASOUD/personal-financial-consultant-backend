import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from src.shared.domain.currency import Currency


class LiabilityBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    liability_type: str = Field(
        ..., description="mortgage, auto_loan, student_loan, personal_loan, credit_card"
    )
    lender: str | None = Field(None, max_length=100)
    interest_rate_percent: Decimal = Field(..., ge=0, le=100)
    monthly_payment: Decimal = Field(..., ge=0)
    start_date: date
    maturity_date: date | None = None
    currency: Currency = Field(default=Currency.USD)


class LiabilityCreate(LiabilityBase):
    original_principal: Decimal = Field(..., gt=0)
    current_balance: Decimal | None = None


class LiabilityUpdate(BaseModel):
    name: str | None = None
    current_balance: Decimal | None = None
    interest_rate_percent: Decimal | None = None
    monthly_payment: Decimal | None = None
    maturity_date: date | None = None


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
