import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import ROUND_HALF_EVEN, Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.app.core.exceptions import AuthenticationException
from src.app.database.models import (
    AccountModel,
    AssetPositionModel,
    CashflowEntryModel,
    HistoricalSnapshotModel,
    LiabilityModel,
    TransactionModel,
    UserModel,
)
from src.modules.analytics.application.dtos import (
    AttentionItem,
    HistoricalSnapshotResponse,
    OverviewDashboardResponse,
)


class AnalyticsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_overview(
        self, current_user: UserModel | None = None
    ) -> OverviewDashboardResponse:
        if current_user is None:
            raise AuthenticationException("Authentication required. Please log in.")

        # Check if user has personal onboarding state (0 baseline for all new users until entered)
        if not current_user.has_completed_financial_onboarding:
            # Newly registered user: All cards and charts start at 0 baseline
            return OverviewDashboardResponse(
                net_worth=Decimal("0.0000"),
                total_assets=Decimal("0.0000"),
                total_liabilities=Decimal("0.0000"),
                liquid_cash=Decimal("0.0000"),
                invested_capital=Decimal("0.0000"),
                currency="TOMAN",
                monthly_income=Decimal("0.0000"),
                monthly_expenses=Decimal("0.0000"),
                monthly_debt_service=Decimal("0.0000"),
                monthly_free_cashflow=Decimal("0.0000"),
                asset_allocation=[],
                liability_breakdown=[],
                attention_items=[
                    AttentionItem(
                        id="welcome-onboarding",
                        severity="info",
                        title="تکمیل پروفایل مالی",
                        message="برای مشاهده شاخص‌ها و پیشنهادهای شخصی‌سازی شده سرمایه‌گذاری، اطلاعات مالی و آزمون سنجش ریسک خود را تکمیل نمایید.",
                        category="onboarding",
                        action_link="/profile",
                    )
                ],
                recent_transactions=[],
                upcoming_obligations=[],
            )
        else:
            # User completed onboarding: personalize overview from user's financial profile
            u_income = (current_user.monthly_income or Decimal("0.0000")).quantize(
                Decimal("0.0001"), rounding=ROUND_HALF_EVEN
            )
            u_liquid = (current_user.liquid_assets or Decimal("0.0000")).quantize(
                Decimal("0.0001"), rounding=ROUND_HALF_EVEN
            )
            u_invested = (current_user.investment_assets or Decimal("0.0000")).quantize(
                Decimal("0.0001"), rounding=ROUND_HALF_EVEN
            )
            u_liabilities = (current_user.total_liabilities or Decimal("0.0000")).quantize(
                Decimal("0.0001"), rounding=ROUND_HALF_EVEN
            )
            u_total_assets = u_liquid + u_invested
            u_net_worth = u_total_assets - u_liabilities
            u_debt_service = (
                (u_liabilities * Decimal("0.05")).quantize(
                    Decimal("0.0001"), rounding=ROUND_HALF_EVEN
                )
                if u_liabilities > 0
                else Decimal("0.0000")
            )
            u_free_cashflow = u_income - u_debt_service

            u_allocation = []
            if u_total_assets > Decimal("0"):
                liq_pct = ((u_liquid / u_total_assets) * Decimal("100")).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_EVEN
                )
                inv_pct = ((u_invested / u_total_assets) * Decimal("100")).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_EVEN
                )
                if u_liquid > 0:
                    u_allocation.append(
                        {
                            "category": "نقدینگی و پس‌انداز",
                            "amount": float(u_liquid),
                            "percentage": float(liq_pct),
                        }
                    )
                if u_invested > 0:
                    u_allocation.append(
                        {
                            "category": "دارایی‌های سرمایه‌گذاری",
                            "amount": float(u_invested),
                            "percentage": float(inv_pct),
                        }
                    )

            u_liability_breakdown = []
            if u_liabilities > Decimal("0"):
                u_liability_breakdown.append(
                    {
                        "category": "تعهدات و بدهی‌ها",
                        "amount": float(u_liabilities),
                        "percentage": 100.0,
                    }
                )

            u_attention = []
            if current_user.risk_level:
                u_attention.append(
                    AttentionItem(
                        id="risk-profile-status",
                        severity="info",
                        title=f"پروفایل ریسک: {current_user.risk_level}",
                        message=f"بر اساس نتایج آزمون روانشناسی مالی، استراتژی سبد شما تنظیم گردیده است (امتیاز: {current_user.risk_score or 0}/100).",
                        category="risk",
                        action_link="/profile",
                    )
                )

            # Query obligations specifically for this user
            liab_stmt = select(LiabilityModel).where(LiabilityModel.user_id == current_user.id)
            liab_res = await self.db.execute(liab_stmt)
            user_liabs = liab_res.scalars().all()
            user_obligations = [
                {
                    "id": str(liab.id),
                    "name": liab.name,
                    "monthly_payment": float(liab.monthly_payment),
                    "remaining_balance": float(liab.current_balance),
                    "due_day": liab.start_date.day,
                }
                for liab in user_liabs
            ]

            # Query recent transactions specifically for this user
            tx_stmt = (
                select(TransactionModel)
                .join(AccountModel, TransactionModel.account_id == AccountModel.id)
                .options(selectinload(TransactionModel.account))
                .where(AccountModel.user_id == current_user.id)
                .order_by(TransactionModel.transaction_date.desc())
                .limit(5)
            )
            tx_res = await self.db.execute(tx_stmt)
            user_txs = [
                {
                    "id": str(t.id),
                    "account_name": t.account.name if t.account else "حساب",
                    "type": t.transaction_type,
                    "amount": float(t.total_amount),
                    "date": t.transaction_date.isoformat(),
                    "currency": t.currency,
                    "notes": t.notes,
                }
                for t in tx_res.scalars().all()
            ]

            return OverviewDashboardResponse(
                net_worth=u_net_worth,
                total_assets=u_total_assets,
                total_liabilities=u_liabilities,
                liquid_cash=u_liquid,
                invested_capital=u_invested,
                currency="TOMAN",
                monthly_income=u_income,
                monthly_expenses=Decimal("0.0000"),
                monthly_debt_service=u_debt_service,
                monthly_free_cashflow=u_free_cashflow,
                asset_allocation=u_allocation,
                liability_breakdown=u_liability_breakdown,
                attention_items=u_attention,
                recent_transactions=user_txs,
                upcoming_obligations=user_obligations,
            )

        # Default system/sysmanager calculation (seeded accounts, positions, liabilities)
        # 1. Accounts & Liquid Cash
        acc_stmt = select(AccountModel).where(AccountModel.is_active == True)  # noqa: E712
        acc_result = await self.db.execute(acc_stmt)
        accounts = acc_result.scalars().all()

        liquid_cash = Decimal("0.0000")
        total_account_cash = Decimal("0.0000")
        for acc in accounts:
            total_account_cash += acc.current_balance
            if acc.account_type.lower() in ("checking", "savings", "cash"):
                liquid_cash += acc.current_balance

        # 2. Asset Positions & Valuation
        pos_stmt = select(AssetPositionModel).options(selectinload(AssetPositionModel.asset))
        pos_result = await self.db.execute(pos_stmt)
        positions = pos_result.scalars().all()

        invested_value = Decimal("0.0000")
        allocation_map: dict[str, Decimal] = {"Cash": liquid_cash}

        for pos in positions:
            val = (pos.quantity * pos.asset.current_price).quantize(
                Decimal("0.0001"), rounding=ROUND_HALF_EVEN
            )
            invested_value += val
            cls_name = pos.asset.asset_class.title()
            allocation_map[cls_name] = allocation_map.get(cls_name, Decimal("0.0000")) + val

        total_assets = total_account_cash + invested_value

        # 3. Liabilities
        liab_stmt = select(LiabilityModel)
        liab_result = await self.db.execute(liab_stmt)
        liabilities = liab_result.scalars().all()

        total_liabilities = Decimal("0.0000")
        monthly_debt_service = Decimal("0.0000")
        liab_breakdown_map: dict[str, Decimal] = {}

        for liab in liabilities:
            total_liabilities += liab.current_balance
            monthly_debt_service += liab.monthly_payment
            l_type = liab.liability_type.replace("_", " ").title()
            liab_breakdown_map[l_type] = (
                liab_breakdown_map.get(l_type, Decimal("0.0000")) + liab.current_balance
            )

        net_worth = total_assets - total_liabilities

        # 4. Monthly Cashflow (Last 30 days)
        thirty_days_ago = date.today() - timedelta(days=30)
        cf_stmt = select(CashflowEntryModel).where(CashflowEntryModel.entry_date >= thirty_days_ago)
        cf_result = await self.db.execute(cf_stmt)
        cf_entries = cf_result.scalars().all()

        monthly_income = Decimal("0.0000")
        monthly_expenses = Decimal("0.0000")
        for cf in cf_entries:
            if cf.flow_type == "income":
                monthly_income += cf.amount
            else:
                monthly_expenses += cf.amount

        monthly_free_cashflow = monthly_income - monthly_expenses - monthly_debt_service

        # 5. Asset Allocation Format
        asset_allocation = []
        for k, v in allocation_map.items():
            pct = Decimal("0.00")
            if total_assets > Decimal("0"):
                pct = ((v / total_assets) * Decimal("100")).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_EVEN
                )
            asset_allocation.append({"category": k, "amount": float(v), "percentage": float(pct)})

        # 6. Liability Breakdown Format
        liability_breakdown = []
        for k, v in liab_breakdown_map.items():
            pct = Decimal("0.00")
            if total_liabilities > Decimal("0"):
                pct = ((v / total_liabilities) * Decimal("100")).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_EVEN
                )
            liability_breakdown.append(
                {"category": k, "amount": float(v), "percentage": float(pct)}
            )

        # 7. Attention Items (Anomalies / Rule-based insights)
        attention_items: list[AttentionItem] = []

        # Check emergency fund buffer (3x monthly expenses)
        emergency_target = (monthly_expenses + monthly_debt_service) * Decimal("3")
        if emergency_target > Decimal("0") and liquid_cash < emergency_target:
            attention_items.append(
                AttentionItem(
                    id="low-liquid-buffer",
                    severity="warning",
                    title="Liquidity Buffer Notice",
                    message=f"Liquid cash (${float(liquid_cash):,.2f}) is below the recommended 3-month expense buffer (${float(emergency_target):,.2f}).",
                    category="liquidity",
                    action_link="/cashflow",
                )
            )

        # Check high interest liabilities
        for liab in liabilities:
            if liab.interest_rate_percent >= Decimal("10.0"):
                attention_items.append(
                    AttentionItem(
                        id=f"high-rate-{liab.id}",
                        severity="critical"
                        if liab.interest_rate_percent > Decimal("18.0")
                        else "warning",
                        title=f"High Interest Obligation: {liab.name}",
                        message=f"{liab.name} carries a {liab.interest_rate_percent}% APR. Consider accelerated repayment.",
                        category="liability",
                        action_link="/liabilities",
                    )
                )

        # Check asset concentration (>35% in single holding)
        for pos in positions:
            pos_val = pos.quantity * pos.asset.current_price
            if total_assets > Decimal("0"):
                concentration = (pos_val / total_assets) * Decimal("100")
                if concentration > Decimal("35.0"):
                    attention_items.append(
                        AttentionItem(
                            id=f"concentration-{pos.asset.symbol}",
                            severity="info",
                            title=f"High Concentration: {pos.asset.symbol}",
                            message=f"{pos.asset.name} ({pos.asset.symbol}) accounts for {float(concentration):.1f}% of total assets.",
                            category="portfolio",
                            action_link="/portfolio",
                        )
                    )

        # 8. Recent Transactions
        tx_stmt = (
            select(TransactionModel)
            .options(selectinload(TransactionModel.account))
            .order_by(TransactionModel.transaction_date.desc())
            .limit(5)
        )
        tx_result = await self.db.execute(tx_stmt)
        recent_txs = [
            {
                "id": str(t.id),
                "account_name": t.account.name if t.account else "حساب",
                "type": t.transaction_type,
                "amount": float(t.total_amount),
                "date": t.transaction_date.isoformat(),
                "currency": t.currency,
                "notes": t.notes,
            }
            for t in tx_result.scalars().all()
        ]

        # 9. Upcoming Obligations
        upcoming_obligations = [
            {
                "id": str(liab.id),
                "name": liab.name,
                "monthly_payment": float(liab.monthly_payment),
                "remaining_balance": float(liab.current_balance),
                "due_day": liab.start_date.day,
            }
            for liab in liabilities
        ]

        return OverviewDashboardResponse(
            net_worth=net_worth.quantize(Decimal("0.0001"), rounding=ROUND_HALF_EVEN),
            total_assets=total_assets.quantize(Decimal("0.0001"), rounding=ROUND_HALF_EVEN),
            total_liabilities=total_liabilities.quantize(
                Decimal("0.0001"), rounding=ROUND_HALF_EVEN
            ),
            liquid_cash=liquid_cash.quantize(Decimal("0.0001"), rounding=ROUND_HALF_EVEN),
            invested_capital=invested_value.quantize(Decimal("0.0001"), rounding=ROUND_HALF_EVEN),
            currency="USD",
            monthly_income=monthly_income.quantize(Decimal("0.0001"), rounding=ROUND_HALF_EVEN),
            monthly_expenses=monthly_expenses.quantize(Decimal("0.0001"), rounding=ROUND_HALF_EVEN),
            monthly_debt_service=monthly_debt_service.quantize(
                Decimal("0.0001"), rounding=ROUND_HALF_EVEN
            ),
            monthly_free_cashflow=monthly_free_cashflow.quantize(
                Decimal("0.0001"), rounding=ROUND_HALF_EVEN
            ),
            asset_allocation=asset_allocation,
            liability_breakdown=liability_breakdown,
            attention_items=attention_items,
            recent_transactions=recent_txs,
            upcoming_obligations=upcoming_obligations,
        )

    async def get_historical_snapshots(
        self, limit: int = 90, current_user: UserModel | None = None
    ) -> list[HistoricalSnapshotResponse]:
        if current_user is None:
            raise AuthenticationException("Authentication required. Please log in.")

        now = datetime.now(UTC)
        today = date.today()
        days = min(limit, 30)

        if not current_user.has_completed_financial_onboarding:
            # Return empty list so charts show proper empty state for new user
            return []
        else:
            # Snapshots reflecting user's financial profile
            u_liquid = current_user.liquid_assets or Decimal("0.0000")
            u_invested = current_user.investment_assets or Decimal("0.0000")
            u_liab = current_user.total_liabilities or Decimal("0.0000")
            u_assets = u_liquid + u_invested
            u_net = u_assets - u_liab
            return [
                HistoricalSnapshotResponse(
                    id=uuid.uuid4(),
                    snapshot_date=today - timedelta(days=i),
                    total_assets=u_assets,
                    total_liabilities=u_liab,
                    net_worth=u_net,
                    liquid_assets=u_liquid,
                    currency="TOMAN",
                    created_at=now,
                )
                for i in reversed(range(days))
            ]

    async def record_snapshot(
        self, snapshot_date: date | None = None, current_user: UserModel | None = None
    ) -> HistoricalSnapshotModel:
        target_date = snapshot_date or date.today()
        overview = await self.get_overview(current_user=current_user)

        # Check existing snapshot for date
        stmt = select(HistoricalSnapshotModel).where(
            HistoricalSnapshotModel.snapshot_date == target_date
        )
        result = await self.db.execute(stmt)
        snapshot = result.scalar_one_or_none()

        if snapshot:
            snapshot.total_assets = overview.total_assets
            snapshot.total_liabilities = overview.total_liabilities
            snapshot.net_worth = overview.net_worth
            snapshot.liquid_assets = overview.liquid_cash
            snapshot.currency = "TOMAN"
        else:
            snapshot = HistoricalSnapshotModel(
                snapshot_date=target_date,
                total_assets=overview.total_assets,
                total_liabilities=overview.total_liabilities,
                net_worth=overview.net_worth,
                liquid_assets=overview.liquid_cash,
                currency="TOMAN",
            )
            self.db.add(snapshot)

        await self.db.flush()
        await self.db.refresh(snapshot)
        return snapshot
