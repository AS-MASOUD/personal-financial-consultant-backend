import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.database.models import UserModel
from src.app.database.session import get_db_session
from src.modules.auth.presentation.dependencies import get_current_user
from src.modules.goals.application.dtos import (
    GoalCategoryCreate,
    GoalCategoryResponse,
    GoalCreate,
    GoalResponse,
    GoalUpdate,
)
from src.modules.goals.application.services import GoalService

goals_router = APIRouter(prefix="/goals", tags=["Goals"])


def get_goal_service(db: AsyncSession = Depends(get_db_session)) -> GoalService:
    return GoalService(db)


@goals_router.get("/categories", response_model=list[GoalCategoryResponse])
async def list_goal_categories(
    service: GoalService = Depends(get_goal_service),
) -> list[GoalCategoryResponse]:
    """List all active financial goal categories."""
    categories = await service.list_goal_categories()
    return [GoalCategoryResponse.model_validate(c) for c in categories]


@goals_router.post(
    "/categories",
    response_model=GoalCategoryResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_goal_category(
    payload: GoalCategoryCreate,
    service: GoalService = Depends(get_goal_service),
) -> GoalCategoryResponse:
    """Create a new financial goal category."""
    cat = await service.create_goal_category(payload)
    return GoalCategoryResponse.model_validate(cat)


@goals_router.get("", response_model=list[GoalResponse])
async def list_goals(
    current_user: UserModel = Depends(get_current_user),
    service: GoalService = Depends(get_goal_service),
) -> list[GoalResponse]:
    return await service.list_goals(current_user=current_user)


@goals_router.post("", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
async def create_goal(
    payload: GoalCreate,
    current_user: UserModel = Depends(get_current_user),
    service: GoalService = Depends(get_goal_service),
) -> GoalResponse:
    return await service.create_goal(payload, current_user=current_user)


@goals_router.patch("/{goal_id}", response_model=GoalResponse)
async def update_goal(
    goal_id: uuid.UUID,
    payload: GoalUpdate,
    current_user: UserModel = Depends(get_current_user),
    service: GoalService = Depends(get_goal_service),
) -> GoalResponse:
    return await service.update_goal(goal_id, payload, current_user=current_user)


@goals_router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_goal(
    goal_id: uuid.UUID,
    current_user: UserModel = Depends(get_current_user),
    service: GoalService = Depends(get_goal_service),
) -> None:
    await service.delete_goal(goal_id, current_user=current_user)
