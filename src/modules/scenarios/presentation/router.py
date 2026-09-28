from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.database.models import UserModel
from src.app.database.session import get_db_session
from src.modules.auth.presentation.dependencies import get_current_user
from src.modules.scenarios.application.dtos import (
    ScenarioSimulationRequest,
    ScenarioSimulationResponse,
)
from src.modules.scenarios.application.services import ScenarioService

scenarios_router = APIRouter(prefix="/scenarios", tags=["Scenario Planning"])


def get_scenario_service(db: AsyncSession = Depends(get_db_session)) -> ScenarioService:
    return ScenarioService(db)


@scenarios_router.post("/simulate", response_model=ScenarioSimulationResponse)
async def simulate_scenario(
    request: ScenarioSimulationRequest,
    current_user: UserModel = Depends(get_current_user),
    service: ScenarioService = Depends(get_scenario_service),
) -> ScenarioSimulationResponse:
    return await service.run_simulation(request, current_user=current_user)
