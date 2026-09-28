import uuid
from datetime import date
from decimal import ROUND_HALF_EVEN, Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.app.core.exceptions import EntityNotFoundException
from src.app.database.models import (
    AccountModel,
    CashflowCategoryModel,
    CashflowEntryModel,
    UserModel,
)
from src.modules.cashflow.application.dtos import (
    CashflowEntryCreate,
    CashflowEntryResponse,
    CashflowSummary,
    CategoryCreate,
)


class CashflowService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_categories(self, flow_type: str | None = None) -> list[CashflowCategoryModel]:
        stmt = select(CashflowCategoryModel)
        if flow_type:
            stmt = stmt.where(CashflowCategoryModel.flow_type == flow_type)
        stmt = stmt.order_by(CashflowCategoryModel.name)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create_category(self, payload: CategoryCreate) -> CashflowCategoryModel:
        category = CashflowCategoryModel(
            name=payload.name,
            flow_type=payload.flow_type.lower(),
            color_hex=payload.color_hex,
            icon=payload.icon,
            monthly_budget=payload.monthly_budget,
        )
        self.db.add(category)
        await self.db.flush()
        await self.db.refresh(category)
        return category

    async def list_entries(
        self,
        current_user: UserModel,
        start_date: date | None = None,
        end_date: date | None = None,
        category_id: uuid.UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[CashflowEntryResponse]:
        stmt = (
            select(CashflowEntryModel)
            .join(AccountModel, CashflowEntryModel.account_id == AccountModel.id)
            .where(AccountModel.user_id == current_user.id)
            .options(selectinload(CashflowEntryModel.category))
        )
        if start_date:
            stmt = stmt.where(CashflowEntryModel.entry_date >= start_date)
        if end_date:
            stmt = stmt.where(CashflowEntryModel.entry_date <= end_date)
        if category_id:
            stmt = stmt.where(CashflowEntryModel.category_id == category_id)
        stmt = stmt.order_by(CashflowEntryModel.entry_date.desc()).limit(limit).offset(offset)
        result = await self.db.execute(stmt)
        entries = result.scalars().all()

        return [
            CashflowEntryResponse(
                id=e.id,
                account_id=e.account_id,
                category_id=e.category_id,
                flow_type=e.flow_type,
                amount=e.amount,
                currency=e.currency,
                entry_date=e.entry_date,
                description=e.description,
                is_recurring=e.is_recurring,
                category_name=e.category.name if e.category else None,
                category_color=e.category.color_hex if e.category else None,
            )
            for e in entries
        ]

    async def create_entry(
        self, payload: CashflowEntryCreate, current_user: UserModel
    ) -> CashflowEntryModel:
        cat_stmt = select(CashflowCategoryModel).where(
            CashflowCategoryModel.id == payload.category_id
        )
        cat_result = await self.db.execute(cat_stmt)
        category = cat_result.scalar_one_or_none()
        if not category:
            raise EntityNotFoundException("CashflowCategory", payload.category_id)

        target_account_id = payload.account_id
        if target_account_id:
            acc_stmt = select(AccountModel).where(
                AccountModel.id == target_account_id,
                AccountModel.user_id == current_user.id,
            )
            acc_res = await self.db.execute(acc_stmt)
            if not acc_res.scalar_one_or_none():
                raise EntityNotFoundException("Account", target_account_id)
        else:
            acc_stmt = select(AccountModel).where(AccountModel.user_id == current_user.id)
            acc_res = await self.db.execute(acc_stmt)
            user_account = acc_res.scalars().first()
            if not user_account:
                user_account = AccountModel(
                    user_id=current_user.id,
                    name="حساب اصلی",
                    account_type="cash",
                    currency="TOMAN",
                    current_balance=Decimal("0.0000"),
                )
                self.db.add(user_account)
                await self.db.flush()
            target_account_id = user_account.id

        entry = CashflowEntryModel(
            account_id=target_account_id,
            category_id=payload.category_id,
            flow_type=payload.flow_type.lower(),
            amount=payload.amount,
            currency=payload.currency.value,
            entry_date=payload.entry_date,
            description=payload.description,
            is_recurring=payload.is_recurring,
        )
        self.db.add(entry)
        await self.db.flush()
        await self.db.refresh(entry)
        return entry

    async def get_summary(
        self,
        current_user: UserModel,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> CashflowSummary:
        stmt = (
            select(CashflowEntryModel)
            .join(AccountModel, CashflowEntryModel.account_id == AccountModel.id)
            .where(AccountModel.user_id == current_user.id)
            .options(selectinload(CashflowEntryModel.category))
        )
        if start_date:
            stmt = stmt.where(CashflowEntryModel.entry_date >= start_date)
        if end_date:
            stmt = stmt.where(CashflowEntryModel.entry_date <= end_date)
        result = await self.db.execute(stmt)
        entries = result.scalars().all()

        if not entries:
            if current_user.has_completed_financial_onboarding:
                total_income = current_user.monthly_income or Decimal("0.0000")
                total_liab = current_user.total_liabilities or Decimal("0.0000")
                debt_service = (total_liab * Decimal("0.05")).quantize(
                    Decimal("0.0001"), rounding=ROUND_HALF_EVEN
                )
                ess = (total_income * Decimal("0.50")).quantize(
                    Decimal("0.0001"), rounding=ROUND_HALF_EVEN
                )
                disc = (total_income * Decimal("0.30")).quantize(
                    Decimal("0.0001"), rounding=ROUND_HALF_EVEN
                )
                total_expenses = ess + disc + debt_service
                net_savings = total_income - total_expenses
                savings_pct = Decimal("0.00")
                if total_income > Decimal("0"):
                    savings_pct = ((net_savings / total_income) * Decimal("100")).quantize(
                        Decimal("0.01"), rounding=ROUND_HALF_EVEN
                    )
                categories_breakdown = []
                if ess > Decimal("0"):
                    categories_breakdown.append(
                        {
                            "category": "هزینه‌های ضروری معیشتی (تخمینی)",
                            "color": "#f43f5e",
                            "flow_type": "expense",
                            "amount": float(ess),
                        }
                    )
                if disc > Decimal("0"):
                    categories_breakdown.append(
                        {
                            "category": "هزینه‌های متفرقه و رفاهی (تخمینی)",
                            "color": "#fb923c",
                            "flow_type": "expense",
                            "amount": float(disc),
                        }
                    )
                if debt_service > Decimal("0"):
                    categories_breakdown.append(
                        {
                            "category": "اقساط و بازپرداخت تعهدات",
                            "color": "#ef4444",
                            "flow_type": "expense",
                            "amount": float(debt_service),
                        }
                    )
                if total_income > Decimal("0"):
                    categories_breakdown.append(
                        {
                            "category": "حقوق و درآمد ماهانه",
                            "color": "#10b981",
                            "flow_type": "income",
                            "amount": float(total_income),
                        }
                    )
                return CashflowSummary(
                    total_income=total_income.quantize(Decimal("0.0001"), rounding=ROUND_HALF_EVEN),
                    total_expenses=total_expenses.quantize(Decimal("0.0001"), rounding=ROUND_HALF_EVEN),
                    net_savings=net_savings.quantize(Decimal("0.0001"), rounding=ROUND_HALF_EVEN),
                    savings_rate_percent=savings_pct,
                    categories_breakdown=categories_breakdown,
                )
            return CashflowSummary(
                total_income=Decimal("0.0000"),
                total_expenses=Decimal("0.0000"),
                net_savings=Decimal("0.0000"),
                savings_rate_percent=Decimal("0.00"),
                categories_breakdown=[],
            )

        total_income = Decimal("0.0000")
        total_expenses = Decimal("0.0000")
        cat_map: dict[str, dict] = {}

        for e in entries:
            if e.flow_type == "income":
                total_income += e.amount
            else:
                total_expenses += e.amount

            cat_name = e.category.name if e.category else "Uncategorized"
            cat_color = e.category.color_hex if e.category else "#94a3b8"

            if cat_name not in cat_map:
                cat_map[cat_name] = {
                    "category": cat_name,
                    "color": cat_color,
                    "flow_type": e.flow_type,
                    "amount": Decimal("0.0000"),
                }
            cat_map[cat_name]["amount"] += e.amount

        net_savings = total_income - total_expenses
        savings_pct = Decimal("0.00")
        if total_income > Decimal("0"):
            savings_pct = ((net_savings / total_income) * Decimal("100")).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_EVEN
            )

        categories_breakdown = [
            {
                "category": v["category"],
                "color": v["color"],
                "flow_type": v["flow_type"],
                "amount": float(v["amount"]),
            }
            for v in cat_map.values()
        ]

        return CashflowSummary(
            total_income=total_income.quantize(Decimal("0.0001"), rounding=ROUND_HALF_EVEN),
            total_expenses=total_expenses.quantize(Decimal("0.0001"), rounding=ROUND_HALF_EVEN),
            net_savings=net_savings.quantize(Decimal("0.0001"), rounding=ROUND_HALF_EVEN),
            savings_rate_percent=savings_pct,
            categories_breakdown=categories_breakdown,
        )
