import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict


class AttentionItem(BaseModel):
    id: str
    severity: str  # info, warning, critical
    title: str
    message: str
    category: str
    action_link: str | None = None


class OverviewDashboardResponse(BaseModel):
    net_worth: Decimal
    total_assets: Decimal
    total_liabilities: Decimal
    liquid_cash: Decimal
    invested_capital: Decimal
    currency: str
    monthly_income: Decimal
    monthly_expenses: Decimal
    monthly_debt_service: Decimal
    monthly_free_cashflow: Decimal
    asset_allocation: list[dict[str, Any]]
    liability_breakdown: list[dict[str, Any]]
    attention_items: list[AttentionItem]
    recent_transactions: list[dict[str, Any]]
    upcoming_obligations: list[dict[str, Any]]


class HistoricalSnapshotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    snapshot_date: date
    total_assets: Decimal
    total_liabilities: Decimal
    net_worth: Decimal
    liquid_assets: Decimal
    currency: str
    created_at: datetime
