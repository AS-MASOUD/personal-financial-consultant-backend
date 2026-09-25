from decimal import ROUND_HALF_EVEN, Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.analytics.application.services import AnalyticsService
from src.modules.liabilities.application.services import LiabilityService
from src.modules.scenarios.application.dtos import (
    MonthlyProjection,
    ScenarioSimulationRequest,
    ScenarioSimulationResponse,
)


class ScenarioService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def run_simulation(
        self, request: ScenarioSimulationRequest
    ) -> ScenarioSimulationResponse:
        analytics = AnalyticsService(self.db)
        overview = await analytics.get_overview()

        baseline_net_worth = overview.net_worth
        baseline_liquid = overview.liquid_cash
        baseline_invested = overview.invested_capital
        baseline_liabilities = overview.total_liabilities
        baseline_cashflow = overview.monthly_free_cashflow

        # Calculate new loan schedule if requested
        new_loan_pmt = Decimal("0.0000")
        loan_schedule = []
        if request.new_loan_amount > Decimal("0"):
            loan_schedule = LiabilityService.calculate_amortization_schedule(
                principal=request.new_loan_amount,
                annual_rate_percent=request.new_loan_rate_annual,
                term_months=request.new_loan_term_months,
            )
            if loan_schedule:
                new_loan_pmt = Decimal(str(loan_schedule[0]["payment"]))

        # Monthly portfolio return factor
        monthly_return_rate = (request.asset_growth_rate_annual / Decimal("100")) / Decimal("12")

        curr_liquid = baseline_liquid + request.one_time_windfall + request.new_loan_amount
        curr_invested = baseline_invested
        curr_liabilities = baseline_liabilities + request.new_loan_amount

        monthly_projections: list[MonthlyProjection] = []

        new_monthly_cashflow = (
            baseline_cashflow
            + request.monthly_income_delta
            - request.monthly_expense_delta
            - new_loan_pmt
        )

        for m in range(1, request.horizon_months + 1):
            # 1. Invested portfolio compound growth
            growth = curr_invested * monthly_return_rate
            curr_invested += growth

            # 2. Free cashflow accumulated into liquidity
            curr_liquid += new_monthly_cashflow

            # 3. New loan amortization reduction if active
            if m <= len(loan_schedule):
                principal_paid = Decimal(str(loan_schedule[m - 1]["principal"]))
                curr_liabilities = max(Decimal("0.0000"), curr_liabilities - principal_paid)

            proj_net_worth = curr_liquid + curr_invested - curr_liabilities

            monthly_projections.append(
                MonthlyProjection(
                    month=m,
                    projected_net_worth=proj_net_worth.quantize(
                        Decimal("0.01"), rounding=ROUND_HALF_EVEN
                    ),
                    projected_liquid_cash=curr_liquid.quantize(
                        Decimal("0.01"), rounding=ROUND_HALF_EVEN
                    ),
                    projected_liabilities=curr_liabilities.quantize(
                        Decimal("0.01"), rounding=ROUND_HALF_EVEN
                    ),
                    projected_monthly_free_cashflow=new_monthly_cashflow.quantize(
                        Decimal("0.01"), rounding=ROUND_HALF_EVEN
                    ),
                )
            )

        final_nw = (
            monthly_projections[-1].projected_net_worth
            if monthly_projections
            else baseline_net_worth
        )
        net_worth_delta = final_nw - baseline_net_worth

        return ScenarioSimulationResponse(
            scenario_name=request.name,
            baseline_net_worth=baseline_net_worth,
            final_projected_net_worth=final_nw,
            net_worth_delta=net_worth_delta,
            baseline_monthly_cashflow=baseline_cashflow,
            new_monthly_cashflow=new_monthly_cashflow,
            new_loan_monthly_payment=new_loan_pmt,
            monthly_projections=monthly_projections,
        )
