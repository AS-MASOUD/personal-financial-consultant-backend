import math
import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import ROUND_HALF_EVEN, Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.exceptions import AuthenticationException, EntityNotFoundException
from src.app.database.models import FinancialGoalModel, UserModel
from src.modules.goals.application.dtos import GoalCreate, GoalResponse, GoalUpdate
from src.shared.domain.currency import Currency


class GoalService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_goals(self, current_user: UserModel | None = None) -> list[GoalResponse]:
        if current_user is None:
            raise AuthenticationException("Authentication required. Please log in.")

        if not current_user.financial_goals:
            return []

        responses: list[GoalResponse] = []
        today = date.today()
        for g in current_user.financial_goals:
            if isinstance(g, str):
                g_title = g
                g_target = Decimal("0.0000")
                g_current = Decimal("0.0000")
                g_monthly = Decimal("0.0000")
                g_cur = Currency.TOMAN
                g_id = uuid.uuid4()
                g_tdate = today + timedelta(days=365 * 2)
                g_status = "in_progress"
                g_notes = "ثبت شده در پرونده مالی"
            else:
                g_title = str(g.get("name", "هدف مالی"))
                g_target = Decimal(str(g.get("target_amount", 0)))
                g_current = Decimal(str(g.get("current_amount", 0)))
                g_monthly = Decimal(str(g.get("monthly_contribution", 0)))
                raw_cur = str(g.get("currency", "TOMAN"))
                g_cur = Currency.TOMAN if raw_cur in ("TOMAN", "USD", "IRR") else Currency.default()
                g_id = uuid.UUID(g["id"]) if "id" in g and g["id"] else uuid.uuid4()
                try:
                    g_tdate = date.fromisoformat(g["target_date"]) if "target_date" in g else (today + timedelta(days=365 * 2))
                except Exception:
                    g_tdate = today + timedelta(days=365 * 2)
                g_status = str(g.get("status", "in_progress"))
                g_notes = str(g.get("notes", "ثبت شده در پرونده مالی"))

            remaining = max(Decimal("0.0000"), g_target - g_current)
            progress_pct = Decimal("0.00")
            if g_target > Decimal("0"):
                progress_pct = ((g_current / g_target) * Decimal("100")).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_EVEN
                )

            projected_date: date | None = None
            if g_monthly > Decimal("0") and remaining > Decimal("0"):
                months_needed = math.ceil(remaining / g_monthly)
                projected_date = today + timedelta(days=months_needed * 30)

            responses.append(
                GoalResponse(
                    id=g_id,
                    name=g_title,
                    category="personal",
                    target_amount=g_target,
                    current_amount=g_current,
                    currency=g_cur,
                    target_date=g_tdate,
                    monthly_contribution=g_monthly,
                    status=g_status,
                    notes=g_notes,
                    created_at=datetime.now(UTC),
                    updated_at=datetime.now(UTC),
                    progress_percent=progress_pct,
                    remaining_amount=remaining.quantize(
                        Decimal("0.0001"), rounding=ROUND_HALF_EVEN
                    ),
                    projected_completion_date=projected_date,
                )
            )
        return responses

    async def create_goal(
        self, payload: GoalCreate, current_user: UserModel | None = None
    ) -> GoalResponse:
        if current_user is None:
            raise AuthenticationException("Authentication required. Please log in.")

        today = date.today()
        user_goals = list(current_user.financial_goals or [])
        goal_id = uuid.uuid4()
        cur_str = payload.currency.value if payload.currency else "TOMAN"
        goal_dict = {
            "id": str(goal_id),
            "name": payload.name,
            "category": payload.category,
            "target_amount": str(payload.target_amount),
            "current_amount": str(payload.current_amount),
            "currency": cur_str,
            "target_date": payload.target_date.isoformat(),
            "monthly_contribution": str(payload.monthly_contribution),
            "status": payload.status,
            "notes": payload.notes,
        }
        user_goals.append(goal_dict)
        current_user.financial_goals = user_goals
        await self.db.flush()

        remaining = max(Decimal("0.0000"), payload.target_amount - payload.current_amount)
        progress_pct = Decimal("0.00")
        if payload.target_amount > Decimal("0"):
            progress_pct = ((payload.current_amount / payload.target_amount) * Decimal("100")).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_EVEN
            )

        projected_date: date | None = None
        if payload.monthly_contribution > Decimal("0") and remaining > Decimal("0"):
            months_needed = math.ceil(remaining / payload.monthly_contribution)
            projected_date = today + timedelta(days=months_needed * 30)

        return GoalResponse(
            id=goal_id,
            name=payload.name,
            category=payload.category,
            target_amount=payload.target_amount,
            current_amount=payload.current_amount,
            currency=Currency(cur_str),
            target_date=payload.target_date,
            monthly_contribution=payload.monthly_contribution,
            status=payload.status,
            notes=payload.notes,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            progress_percent=progress_pct,
            remaining_amount=remaining.quantize(
                Decimal("0.0001"), rounding=ROUND_HALF_EVEN
            ),
            projected_completion_date=projected_date,
        )

    async def update_goal(self, goal_id: uuid.UUID, payload: GoalUpdate) -> FinancialGoalModel:
        stmt = select(FinancialGoalModel).where(FinancialGoalModel.id == goal_id)
        result = await self.db.execute(stmt)
        goal = result.scalar_one_or_none()
        if not goal:
            raise EntityNotFoundException("FinancialGoal", goal_id)

        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(goal, field, value)
        await self.db.flush()
        await self.db.refresh(goal)
        return goal
