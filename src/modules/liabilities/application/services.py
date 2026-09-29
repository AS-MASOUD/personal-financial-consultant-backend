from decimal import ROUND_HALF_EVEN, Decimal
from typing import Any
import uuid

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.exceptions import (
    EntityConflictException,
    EntityNotFoundException,
    FinancialCalculationException,
)
from src.app.database.models import (
    LiabilityModel,
    LiabilityPaymentModel,
    LiabilityTypeModel,
    UserModel,
)
from src.modules.liabilities.application.dtos import (
    LiabilityCreate,
    LiabilityPaymentCreate,
    LiabilityResponse,
    LiabilityTypeCreate,
    LiabilityTypeResponse,
    LiabilityUpdate,
)
from src.shared.domain.currency import Currency


class LiabilityService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_liability_types(self, include_inactive: bool = False) -> list[LiabilityTypeModel]:
        stmt = select(LiabilityTypeModel).order_by(
            LiabilityTypeModel.display_order.asc(),
            LiabilityTypeModel.created_at.asc(),
        )
        if not include_inactive:
            stmt = stmt.where(LiabilityTypeModel.is_active.is_(True))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_liability_labels(self) -> dict[str, str]:
        types = await self.list_liability_types(include_inactive=True)
        return {t.code: (t.short_label or t.label) for t in types}

    async def create_liability_type(self, payload: LiabilityTypeCreate) -> LiabilityTypeModel:
        stmt = select(LiabilityTypeModel).where(LiabilityTypeModel.code == payload.code)
        existing = await self.db.execute(stmt)
        if existing.scalar_one_or_none():
            raise EntityConflictException(f"Liability type with code '{payload.code}' already exists")

        new_type = LiabilityTypeModel(
            code=payload.code,
            label=payload.label,
            short_label=payload.short_label,
            description=payload.description,
            icon=payload.icon,
            default_rate=payload.default_rate,
            default_term_months=payload.default_term_months,
            is_friend=payload.is_friend,
            direction=payload.direction,
            display_order=payload.display_order,
            is_active=payload.is_active,
        )
        self.db.add(new_type)
        await self.db.flush()
        return new_type

    async def list_liabilities(self, current_user: UserModel) -> list[LiabilityResponse]:
        stmt = (
            select(LiabilityModel)
            .options(selectinload(LiabilityModel.type_config))
            .where(LiabilityModel.user_id == current_user.id)
            .order_by(LiabilityModel.current_balance.desc())
        )
        result = await self.db.execute(stmt)
        liabilities = result.scalars().all()

        responses: list[LiabilityResponse] = []
        for liab in liabilities:
            repaid = liab.original_principal - liab.current_balance
            repaid_pct = Decimal("0.00")
            if liab.original_principal > Decimal("0"):
                repaid_pct = ((repaid / liab.original_principal) * Decimal("100")).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_EVEN
                )
            responses.append(
                LiabilityResponse(
                    id=liab.id,
                    name=liab.name,
                    liability_type=liab.liability_type,
                    lender=liab.lender,
                    original_principal=liab.original_principal,
                    current_balance=liab.current_balance,
                    interest_rate_percent=liab.interest_rate_percent,
                    monthly_payment=liab.monthly_payment,
                    start_date=liab.start_date,
                    maturity_date=liab.maturity_date,
                    currency=Currency(liab.currency),
                    created_at=liab.created_at,
                    updated_at=liab.updated_at,
                    repaid_amount=repaid.quantize(Decimal("0.0001"), rounding=ROUND_HALF_EVEN),
                    repaid_percent=repaid_pct,
                    type_config=LiabilityTypeResponse.model_validate(liab.type_config)
                    if liab.type_config
                    else None,
                )
            )
        return responses

    async def create_liability(self, payload: LiabilityCreate, current_user: UserModel) -> LiabilityModel:
        curr_balance = (
            payload.current_balance
            if payload.current_balance is not None
            else payload.original_principal
        )

        mat_date = payload.maturity_date
        if not mat_date and payload.term_months:
            from datetime import timedelta
            mat_date = payload.start_date + timedelta(days=payload.term_months * 30)

        m_payment = payload.monthly_payment
        if (m_payment is None or m_payment == Decimal("0")) and payload.term_months and payload.term_months > 0:
            if payload.interest_rate_percent == Decimal("0"):
                m_payment = (payload.original_principal / Decimal(payload.term_months)).quantize(
                    Decimal("0.0001"), rounding=ROUND_HALF_EVEN
                )
            else:
                r = (payload.interest_rate_percent / Decimal("100")) / Decimal("12")
                n = Decimal(payload.term_months)
                factor = (Decimal("1") + r) ** n
                if factor > Decimal("1"):
                    m_payment = (payload.original_principal * (r * factor) / (factor - Decimal("1"))).quantize(
                        Decimal("0.0001"), rounding=ROUND_HALF_EVEN
                    )
                else:
                    m_payment = (payload.original_principal / Decimal(payload.term_months)).quantize(
                        Decimal("0.0001"), rounding=ROUND_HALF_EVEN
                    )

        liability = LiabilityModel(
            user_id=current_user.id,
            name=payload.name,
            liability_type=payload.liability_type,
            lender=payload.lender,
            original_principal=payload.original_principal,
            current_balance=curr_balance,
            interest_rate_percent=payload.interest_rate_percent,
            monthly_payment=m_payment,
            start_date=payload.start_date,
            maturity_date=mat_date,
            currency=payload.currency.value,
        )
        self.db.add(liability)
        await self.db.flush()
        await self.db.refresh(liability, ["type_config"])
        return liability

    async def update_liability(
        self, liability_id: uuid.UUID, payload: LiabilityUpdate, current_user: UserModel
    ) -> LiabilityModel:
        stmt = (
            select(LiabilityModel)
            .options(selectinload(LiabilityModel.type_config))
            .where(
                LiabilityModel.id == liability_id,
                LiabilityModel.user_id == current_user.id,
            )
        )
        result = await self.db.execute(stmt)
        liability = result.scalar_one_or_none()
        if not liability:
            raise EntityNotFoundException("Liability", liability_id)

        update_data = payload.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if key == "currency" and value is not None:
                liability.currency = value.value if hasattr(value, "value") else str(value)
            elif value is not None:
                setattr(liability, key, value)

        await self.db.flush()
        await self.db.refresh(liability, ["type_config"])
        return liability

    async def get_liability_payments(
        self, liability_id: uuid.UUID, current_user: UserModel
    ) -> list[LiabilityPaymentModel]:
        stmt = select(LiabilityModel).where(
            LiabilityModel.id == liability_id,
            LiabilityModel.user_id == current_user.id,
        )
        result = await self.db.execute(stmt)
        liability = result.scalar_one_or_none()
        if not liability:
            raise EntityNotFoundException("Liability", liability_id)

        p_stmt = (
            select(LiabilityPaymentModel)
            .where(LiabilityPaymentModel.liability_id == liability_id)
            .order_by(LiabilityPaymentModel.payment_date.desc(), LiabilityPaymentModel.created_at.desc())
        )
        p_res = await self.db.execute(p_stmt)
        return list(p_res.scalars().all())

    async def delete_liability(self, liability_id: uuid.UUID, current_user: UserModel) -> None:
        stmt = select(LiabilityModel).where(
            LiabilityModel.id == liability_id,
            LiabilityModel.user_id == current_user.id,
        )
        result = await self.db.execute(stmt)
        liability = result.scalar_one_or_none()
        if not liability:
            raise EntityNotFoundException("Liability", liability_id)
        await self.db.delete(liability)
        await self.db.flush()

    async def record_payment(
        self, payload: LiabilityPaymentCreate, current_user: UserModel
    ) -> LiabilityPaymentModel:
        stmt = select(LiabilityModel).where(
            LiabilityModel.id == payload.liability_id,
            LiabilityModel.user_id == current_user.id,
        )
        result = await self.db.execute(stmt)
        liability = result.scalar_one_or_none()
        if not liability:
            raise EntityNotFoundException("Liability", payload.liability_id)

        principal_reduction = payload.principal_amount + payload.extra_principal
        if principal_reduction > liability.current_balance:
            principal_reduction = liability.current_balance

        liability.current_balance -= principal_reduction
        total_payment = payload.principal_amount + payload.interest_amount + payload.extra_principal

        payment = LiabilityPaymentModel(
            liability_id=payload.liability_id,
            payment_date=payload.payment_date,
            principal_amount=payload.principal_amount,
            interest_amount=payload.interest_amount,
            extra_principal=payload.extra_principal,
            total_payment=total_payment,
        )
        self.db.add(payment)
        await self.db.flush()
        await self.db.refresh(payment)
        return payment

    @staticmethod
    def calculate_amortization_schedule(
        principal: Decimal,
        annual_rate_percent: Decimal,
        term_months: int,
    ) -> list[dict[str, Any]]:
        """Deterministic loan amortization calculation using Decimal."""
        if term_months <= 0:
            raise FinancialCalculationException("Term must be at least 1 month.")

        monthly_rate = (annual_rate_percent / Decimal("100")) / Decimal("12")
        balance = principal
        schedule = []

        if monthly_rate == Decimal("0"):
            monthly_payment = (principal / Decimal(term_months)).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_EVEN
            )
        else:
            factor = (Decimal("1") + monthly_rate) ** term_months
            monthly_payment = (
                principal * (monthly_rate * factor) / (factor - Decimal("1"))
            ).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)

        for month in range(1, term_months + 1):
            interest = (balance * monthly_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
            principal_part = monthly_payment - interest
            if month == term_months or principal_part > balance:
                principal_part = balance
                monthly_payment = principal_part + interest
            balance = (balance - principal_part).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)

            schedule.append(
                {
                    "month": month,
                    "payment": monthly_payment,
                    "principal": principal_part,
                    "interest": interest,
                    "remaining_balance": max(Decimal("0.00"), balance),
                }
            )
            if balance <= Decimal("0.00"):
                break

        return schedule
