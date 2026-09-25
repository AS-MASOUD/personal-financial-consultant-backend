from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.database.session import get_db_session
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
    service: ScenarioService = Depends(get_scenario_service),
) -> ScenarioSimulationResponse:
    return await service.run_simulation(request)
