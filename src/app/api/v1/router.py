from fastapi import APIRouter

from src.modules.accounts.presentation.router import accounts_router
from src.modules.ai.presentation.router import ai_router
from src.modules.analytics.presentation.router import analytics_router
from src.modules.assets.presentation.router import assets_router
from src.modules.cashflow.presentation.router import cashflow_router
from src.modules.goals.presentation.router import goals_router
from src.modules.liabilities.presentation.router import liabilities_router
from src.modules.scenarios.presentation.router import scenarios_router
from src.modules.transactions.presentation.router import transactions_router

api_v1_router = APIRouter()

api_v1_router.include_router(accounts_router)
api_v1_router.include_router(assets_router)
api_v1_router.include_router(transactions_router)
api_v1_router.include_router(liabilities_router)
api_v1_router.include_router(cashflow_router)
api_v1_router.include_router(goals_router)
api_v1_router.include_router(analytics_router)
api_v1_router.include_router(scenarios_router)
api_v1_router.include_router(ai_router)
