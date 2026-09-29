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


class TrajectoryTimelinePoint(BaseModel):
    date: str
    display_date: str
    is_forecast: bool
    total_liabilities: Decimal
    total_investments: Decimal
    salary_income: Decimal
    net_worth: Decimal
    liquid_cash: Decimal
    forecast_confidence_upper: Decimal | None = None
    forecast_confidence_lower: Decimal | None = None
    item_values: dict[str, Decimal] = {}


class LoanTrajectoryItem(BaseModel):
    id: str
    name: str
    liability_type: str
    lender: str | None = None
    original_principal: Decimal
    current_balance: Decimal
    interest_rate_percent: Decimal
    monthly_payment: Decimal
    start_date: str
    maturity_date: str | None = None
    estimated_payoff_date: str
    remaining_months: int
    repaid_percent: Decimal


class InvestmentTrajectoryItem(BaseModel):
    id: str
    name: str
    symbol: str
    asset_class: str
    current_value: Decimal
    quantity: Decimal
    current_price: Decimal
    unrealized_pnl: Decimal
    projected_annual_growth_rate: Decimal
    projected_value_1y: Decimal
    projected_value_2y: Decimal


class IncomeTrajectoryItem(BaseModel):
    id: str
    name: str
    flow_type: str
    monthly_amount: Decimal
    annual_amount: Decimal
    is_recurring: bool


class WealthTrajectoryResponse(BaseModel):
    timeline: list[TrajectoryTimelinePoint]
    historical_points_count: int
    forecast_points_count: int
    baseline_investments: Decimal
    baseline_liabilities: Decimal
    baseline_salary: Decimal
    debt_free_date: str | None = None
    crossover_date: str | None = None
    projected_investments_end: Decimal
    projected_liabilities_end: Decimal
    projected_total_profit: Decimal
    total_debt_interest_saved: Decimal
    ai_narrative: str
    loans: list[LoanTrajectoryItem]
    investments: list[InvestmentTrajectoryItem]
    incomes: list[IncomeTrajectoryItem]
