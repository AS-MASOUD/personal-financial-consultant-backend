import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from src.shared.domain.currency import Currency


class GoalBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    category: str = Field(
        ...,
        description="emergency_fund, retirement, home_purchase, vacation, education, debt_payoff",
    )
    target_amount: Decimal = Field(..., gt=0)
    current_amount: Decimal = Field(default=Decimal("0.0000"), ge=0)
    currency: Currency = Field(default=Currency.USD)
    target_date: date
    monthly_contribution: Decimal = Field(default=Decimal("0.0000"), ge=0)
    status: str = Field(default="in_progress")
    notes: str | None = None


class GoalCreate(GoalBase):
    pass


class GoalUpdate(BaseModel):
    name: str | None = None
    target_amount: Decimal | None = None
    current_amount: Decimal | None = None
    monthly_contribution: Decimal | None = None
    target_date: date | None = None
    status: str | None = None
    notes: str | None = None


class GoalResponse(GoalBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    progress_percent: Decimal
    remaining_amount: Decimal
    projected_completion_date: date | None = None
