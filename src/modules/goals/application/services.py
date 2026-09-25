import math
import uuid
from datetime import date, timedelta
from decimal import ROUND_HALF_EVEN, Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.exceptions import EntityNotFoundException
from src.app.database.models import FinancialGoalModel
from src.modules.goals.application.dtos import GoalCreate, GoalResponse, GoalUpdate
from src.shared.domain.currency import Currency


class GoalService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_goals(self) -> list[GoalResponse]:
        stmt = select(FinancialGoalModel).order_by(FinancialGoalModel.target_date)
        result = await self.db.execute(stmt)
        goals = result.scalars().all()

        responses: list[GoalResponse] = []
        today = date.today()

        for g in goals:
            remaining = max(Decimal("0.0000"), g.target_amount - g.current_amount)
            progress_pct = Decimal("0.00")
            if g.target_amount > Decimal("0"):
                progress_pct = ((g.current_amount / g.target_amount) * Decimal("100")).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_EVEN
                )

            projected_date: date | None = None
            if g.monthly_contribution > Decimal("0") and remaining > Decimal("0"):
                months_needed = math.ceil(remaining / g.monthly_contribution)
                projected_date = today + timedelta(days=months_needed * 30)

            responses.append(
                GoalResponse(
                    id=g.id,
                    name=g.name,
                    category=g.category,
                    target_amount=g.target_amount,
                    current_amount=g.current_amount,
                    currency=Currency(g.currency),
                    target_date=g.target_date,
                    monthly_contribution=g.monthly_contribution,
                    status=g.status,
                    notes=g.notes,
                    created_at=g.created_at,
                    updated_at=g.updated_at,
                    progress_percent=progress_pct,
                    remaining_amount=remaining.quantize(
                        Decimal("0.0001"), rounding=ROUND_HALF_EVEN
                    ),
                    projected_completion_date=projected_date,
                )
            )
        return responses

    async def create_goal(self, payload: GoalCreate) -> FinancialGoalModel:
        goal = FinancialGoalModel(
            name=payload.name,
            category=payload.category,
            target_amount=payload.target_amount,
            current_amount=payload.current_amount,
            currency=payload.currency.value,
            target_date=payload.target_date,
            monthly_contribution=payload.monthly_contribution,
            status=payload.status,
            notes=payload.notes,
        )
        self.db.add(goal)
        await self.db.flush()
        await self.db.refresh(goal)
        return goal

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
