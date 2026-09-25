from decimal import Decimal

from pydantic import BaseModel, Field


class ScenarioSimulationRequest(BaseModel):
    name: str = Field(default="Custom Financial Scenario")
    horizon_months: int = Field(default=36, ge=1, le=360)
    monthly_income_delta: Decimal = Field(
        default=Decimal("0.0000"), description="Net monthly income adjustment (+ or -)"
    )
    monthly_expense_delta: Decimal = Field(
        default=Decimal("0.0000"), description="Net monthly expense adjustment (+ or -)"
    )
    asset_growth_rate_annual: Decimal = Field(
        default=Decimal("7.0"), ge=-50, le=100, description="Annual portfolio return rate %"
    )
    new_loan_amount: Decimal = Field(default=Decimal("0.0000"), ge=0)
    new_loan_rate_annual: Decimal = Field(default=Decimal("6.5"), ge=0, le=50)
    new_loan_term_months: int = Field(default=60, ge=1, le=360)
    one_time_windfall: Decimal = Field(
        default=Decimal("0.0000"), description="Immediate lump sum (+ or -)"
    )


class MonthlyProjection(BaseModel):
    month: int
    projected_net_worth: Decimal
    projected_liquid_cash: Decimal
    projected_liabilities: Decimal
    projected_monthly_free_cashflow: Decimal


class ScenarioSimulationResponse(BaseModel):
    scenario_name: str
    baseline_net_worth: Decimal
    final_projected_net_worth: Decimal
    net_worth_delta: Decimal
    baseline_monthly_cashflow: Decimal
    new_monthly_cashflow: Decimal
    new_loan_monthly_payment: Decimal
    monthly_projections: list[MonthlyProjection]
