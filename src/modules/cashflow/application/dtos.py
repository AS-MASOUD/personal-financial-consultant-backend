import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from src.shared.domain.currency import Currency


class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    flow_type: str = Field(..., description="income, expense")
    color_hex: str = Field(default="#6366f1", max_length=10)
    icon: str = Field(default="circle", max_length=50)
    monthly_budget: Decimal | None = Field(None, ge=0)


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    flow_type: str
    color_hex: str
    icon: str
    monthly_budget: Decimal | None
    created_at: datetime


class CashflowEntryCreate(BaseModel):
    account_id: uuid.UUID | None = None
    category_id: uuid.UUID
    flow_type: str = Field(..., description="income, expense")
    amount: Decimal = Field(..., gt=0)
    currency: Currency = Field(default=Currency.TOMAN)
    entry_date: date
    description: str = Field(..., min_length=1, max_length=255)
    is_recurring: bool = False


class CashflowEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    account_id: uuid.UUID | None
    category_id: uuid.UUID
    flow_type: str
    amount: Decimal
    currency: str
    entry_date: date
    description: str
    is_recurring: bool
    category_name: str | None = None
    category_color: str | None = None


class CashflowSummary(BaseModel):
    total_income: Decimal
    total_expenses: Decimal
    net_savings: Decimal
    savings_rate_percent: Decimal
    categories_breakdown: list[dict]
