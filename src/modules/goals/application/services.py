import math
import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import ROUND_HALF_EVEN, Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from src.app.core.exceptions import AuthenticationException, EntityConflictException, EntityNotFoundException
from src.app.database.models import GoalCategoryModel, UserModel
from src.modules.goals.application.dtos import (
    GoalCategoryCreate,
    GoalCreate,
    GoalResponse,
    GoalUpdate,
)
from src.shared.domain.currency import Currency


def safe_parse_currency(raw: str | None) -> Currency:
    if not raw:
        return Currency.TOMAN
    upper = raw.upper().strip()
    try:
        return Currency(upper)
    except ValueError:
        return Currency.TOMAN


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
                g_cat = "other"
                g_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"{current_user.id}_{g}")
                g_tdate = today + timedelta(days=365 * 2)
                g_status = "in_progress"
                g_notes = "ثبت شده در پرونده مالی آغازین"
                created_dt = datetime.now(UTC)
            else:
                g_title = str(g.get("name", "هدف مالی"))
                g_cat = str(g.get("category", "other"))
                try:
                    g_target = Decimal(str(g.get("target_amount", 0)))
                except Exception:
                    g_target = Decimal("0.0000")
                try:
                    g_current = Decimal(str(g.get("current_amount", 0)))
                except Exception:
                    g_current = Decimal("0.0000")
                try:
                    g_monthly = Decimal(str(g.get("monthly_contribution", 0)))
                except Exception:
                    g_monthly = Decimal("0.0000")

                g_cur = safe_parse_currency(str(g.get("currency", "TOMAN")))

                if "id" in g and g["id"]:
                    try:
                        g_id = uuid.UUID(str(g["id"]))
                    except Exception:
                        g_id = uuid.uuid4()
                else:
                    g_id = uuid.uuid4()

                if "target_date" in g and g["target_date"]:
                    try:
                        g_tdate = date.fromisoformat(str(g["target_date"]))
                    except Exception:
                        g_tdate = today + timedelta(days=365 * 2)
                else:
                    g_tdate = today + timedelta(days=365 * 2)

                g_status = str(g.get("status", "in_progress"))
                g_notes = g.get("notes") or None

                if "created_at" in g and g["created_at"]:
                    try:
                        created_dt = datetime.fromisoformat(str(g["created_at"]))
                    except Exception:
                        created_dt = datetime.now(UTC)
                else:
                    created_dt = datetime.now(UTC)

            remaining = max(Decimal("0.0000"), g_target - g_current)
            progress_pct = Decimal("0.00")
            if g_target > Decimal("0"):
                progress_pct = ((g_current / g_target) * Decimal("100")).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_EVEN
                )

            projected_date: date | None = None
            if g_monthly > Decimal("0") and remaining > Decimal("0"):
                months_needed = math.ceil(remaining / g_monthly)
                if 0 < months_needed < 1200:
                    projected_date = today + timedelta(days=months_needed * 30)

            responses.append(
                GoalResponse(
                    id=g_id,
                    name=g_title,
                    category=g_cat,
                    target_amount=g_target,
                    current_amount=g_current,
                    currency=g_cur,
                    target_date=g_tdate,
                    monthly_contribution=g_monthly,
                    status=g_status,
                    notes=g_notes,
                    created_at=created_dt,
                    updated_at=created_dt,
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
        now = datetime.now(UTC)

        cur_str = (
            payload.currency.value
            if hasattr(payload.currency, "value")
            else str(payload.currency or "TOMAN")
        )
        cur_obj = safe_parse_currency(cur_str)

        target_date_iso = (
            payload.target_date.isoformat()
            if payload.target_date
            else (today + timedelta(days=365)).isoformat()
        )

        goal_dict = {
            "id": str(goal_id),
            "name": payload.name.strip(),
            "category": payload.category or "other",
            "target_amount": str(payload.target_amount),
            "current_amount": str(payload.current_amount or Decimal("0")),
            "currency": cur_obj.value,
            "target_date": target_date_iso,
            "monthly_contribution": str(payload.monthly_contribution or Decimal("0")),
            "status": payload.status or "in_progress",
            "notes": payload.notes.strip() if payload.notes else None,
            "created_at": now.isoformat(),
        }
        user_goals.append(goal_dict)
        current_user.financial_goals = user_goals
        flag_modified(current_user, "financial_goals")
        await self.db.flush()

        curr_amt = payload.current_amount or Decimal("0")
        remaining = max(Decimal("0.0000"), payload.target_amount - curr_amt)
        progress_pct = Decimal("0.00")
        if payload.target_amount > Decimal("0"):
            progress_pct = ((curr_amt / payload.target_amount) * Decimal("100")).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_EVEN
            )

        projected_date: date | None = None
        monthly = payload.monthly_contribution or Decimal("0")
        if monthly > Decimal("0") and remaining > Decimal("0"):
            months_needed = math.ceil(remaining / monthly)
            if 0 < months_needed < 1200:
                projected_date = today + timedelta(days=months_needed * 30)

        return GoalResponse(
            id=goal_id,
            name=payload.name.strip(),
            category=payload.category or "other",
            target_amount=payload.target_amount,
            current_amount=curr_amt,
            currency=cur_obj,
            target_date=payload.target_date or (today + timedelta(days=365)),
            monthly_contribution=monthly,
            status=payload.status or "in_progress",
            notes=payload.notes.strip() if payload.notes else None,
            created_at=now,
            updated_at=now,
            progress_percent=progress_pct,
            remaining_amount=remaining.quantize(
                Decimal("0.0001"), rounding=ROUND_HALF_EVEN
            ),
            projected_completion_date=projected_date,
        )

    async def update_goal(
        self,
        goal_id: uuid.UUID,
        payload: GoalUpdate,
        current_user: UserModel | None = None,
    ) -> GoalResponse:
        if current_user is None:
            raise AuthenticationException("Authentication required. Please log in.")

        user_goals = list(current_user.financial_goals or [])
        target_idx = -1
        target_goal_dict: dict | None = None

        goal_id_str = str(goal_id)
        for idx, g in enumerate(user_goals):
            if isinstance(g, dict) and str(g.get("id")) == goal_id_str:
                target_idx = idx
                target_goal_dict = g
                break
            elif isinstance(g, str):
                det_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{current_user.id}_{g}"))
                if det_uuid == goal_id_str:
                    target_idx = idx
                    target_goal_dict = {
                        "id": det_uuid,
                        "name": g,
                        "category": "other",
                        "target_amount": "0",
                        "current_amount": "0",
                        "currency": "TOMAN",
                        "status": "in_progress",
                    }
                    break

        if target_idx == -1 or target_goal_dict is None:
            raise EntityNotFoundException("Goal", goal_id)

        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "target_date" and isinstance(value, date):
                target_goal_dict[field] = value.isoformat()
            elif isinstance(value, Decimal):
                target_goal_dict[field] = str(value)
            elif value is not None:
                target_goal_dict[field] = value

        user_goals[target_idx] = target_goal_dict
        current_user.financial_goals = user_goals
        flag_modified(current_user, "financial_goals")
        await self.db.flush()

        # Build response
        goals_list = await self.list_goals(current_user)
        for g in goals_list:
            if str(g.id) == goal_id_str:
                return g

        raise EntityNotFoundException("Goal", goal_id)

    async def delete_goal(
        self,
        goal_id: uuid.UUID,
        current_user: UserModel | None = None,
    ) -> None:
        if current_user is None:
            raise AuthenticationException("Authentication required. Please log in.")

        user_goals = list(current_user.financial_goals or [])
        goal_id_str = str(goal_id)

        updated_goals = []
        found = False
        for g in user_goals:
            if isinstance(g, dict):
                if str(g.get("id")) == goal_id_str:
                    found = True
                    continue
                updated_goals.append(g)
            elif isinstance(g, str):
                det_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{current_user.id}_{g}"))
                if det_uuid == goal_id_str:
                    found = True
                    continue
                updated_goals.append(g)

        if not found:
            raise EntityNotFoundException("Goal", goal_id)

        current_user.financial_goals = updated_goals
        flag_modified(current_user, "financial_goals")
        await self.db.flush()

    # ── Goal Categories (reference data) ──────────────────────────────

    async def list_goal_categories(self) -> list[GoalCategoryModel]:
        stmt = (
            select(GoalCategoryModel)
            .where(GoalCategoryModel.is_active.is_(True))
            .order_by(GoalCategoryModel.display_order)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create_goal_category(self, payload: GoalCategoryCreate) -> GoalCategoryModel:
        stmt = select(GoalCategoryModel).where(GoalCategoryModel.code == payload.code)
        result = await self.db.execute(stmt)
        if result.scalar_one_or_none():
            raise EntityConflictException(
                f"Goal category with code '{payload.code}' already exists."
            )

        cat = GoalCategoryModel(
            code=payload.code,
            label=payload.label,
            description=payload.description,
            icon=payload.icon,
            display_order=payload.display_order,
            is_active=payload.is_active,
        )
        self.db.add(cat)
        await self.db.flush()
        await self.db.refresh(cat)
        return cat
