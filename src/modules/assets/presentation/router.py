import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.database.session import get_db_session
from src.modules.assets.application.dtos import (
    AssetCreate,
    AssetPositionResponse,
    AssetResponse,
    AssetUpdate,
)
from src.modules.assets.application.services import AssetService

assets_router = APIRouter(prefix="/assets", tags=["Assets"])


def get_asset_service(db: AsyncSession = Depends(get_db_session)) -> AssetService:
    return AssetService(db)


@assets_router.get("", response_model=list[AssetResponse])
async def list_assets(
    asset_class: str | None = None,
    service: AssetService = Depends(get_asset_service),
) -> list[AssetResponse]:
    assets = await service.list_assets(asset_class=asset_class)
    return [AssetResponse.model_validate(a) for a in assets]


@assets_router.get("/positions", response_model=list[AssetPositionResponse])
async def list_positions(
    account_id: uuid.UUID | None = None,
    service: AssetService = Depends(get_asset_service),
) -> list[AssetPositionResponse]:
    return await service.list_positions(account_id=account_id)


@assets_router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset(
    asset_id: uuid.UUID,
    service: AssetService = Depends(get_asset_service),
) -> AssetResponse:
    asset = await service.get_asset(asset_id)
    return AssetResponse.model_validate(asset)


@assets_router.post("", response_model=AssetResponse, status_code=status.HTTP_201_CREATED)
async def create_asset(
    payload: AssetCreate,
    service: AssetService = Depends(get_asset_service),
) -> AssetResponse:
    asset = await service.create_asset(payload)
    return AssetResponse.model_validate(asset)


@assets_router.patch("/{asset_id}", response_model=AssetResponse)
async def update_asset(
    asset_id: uuid.UUID,
    payload: AssetUpdate,
    service: AssetService = Depends(get_asset_service),
) -> AssetResponse:
    asset = await service.update_asset(asset_id, payload)
    return AssetResponse.model_validate(asset)


@assets_router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_asset(
    asset_id: uuid.UUID,
    service: AssetService = Depends(get_asset_service),
) -> None:
    await service.delete_asset(asset_id)
