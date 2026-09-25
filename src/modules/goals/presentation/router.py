import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.database.session import get_db_session
from src.modules.goals.application.dtos import GoalCreate, GoalResponse, GoalUpdate
from src.modules.goals.application.services import GoalService

goals_router = APIRouter(prefix="/goals", tags=["Goals"])


def get_goal_service(db: AsyncSession = Depends(get_db_session)) -> GoalService:
    return GoalService(db)


@goals_router.get("", response_model=list[GoalResponse])
async def list_goals(
    service: GoalService = Depends(get_goal_service),
) -> list[GoalResponse]:
    return await service.list_goals()


@goals_router.post("", status_code=status.HTTP_201_CREATED)
async def create_goal(
    payload: GoalCreate,
    service: GoalService = Depends(get_goal_service),
):
    return await service.create_goal(payload)


@goals_router.patch("/{goal_id}")
async def update_goal(
    goal_id: uuid.UUID,
    payload: GoalUpdate,
    service: GoalService = Depends(get_goal_service),
):
    return await service.update_goal(goal_id, payload)
