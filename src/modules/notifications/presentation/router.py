import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.database.models import UserModel
from src.app.database.session import get_db_session
from src.modules.auth.presentation.dependencies import get_current_user, get_optional_current_user
from src.modules.notifications.application.dtos import (
    NotificationListResponse,
    NotificationResponse,
)
from src.modules.notifications.application.services import NotificationService

notifications_router = APIRouter(prefix="/notifications", tags=["Notifications & Market Alerts"])
notification_service = NotificationService()


@notifications_router.get(
    "",
    response_model=NotificationListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get notifications for current user",
)
async def get_notifications(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    unread_only: bool = Query(False),
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> NotificationListResponse:
    """Retrieve notifications, financial milestone alerts, and asset volatility warnings."""
    user_id = current_user.id
    return await notification_service.list_notifications(
        db=db,
        user_id=user_id,
        limit=limit,
        offset=offset,
        unread_only=unread_only,
    )


@notifications_router.patch(
    "/{notification_id}/read",
    response_model=NotificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Mark single notification as read",
)
async def mark_notification_read(
    notification_id: uuid.UUID,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> NotificationResponse:
    """Mark a notification as read for current user."""
    return await notification_service.mark_as_read(
        db=db,
        user_id=current_user.id,
        notification_id=notification_id,
    )


@notifications_router.post(
    "/read-all",
    status_code=status.HTTP_200_OK,
    summary="Mark all notifications as read",
)
async def mark_all_read(
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, int]:
    """Mark all unread notifications as read."""
    count = await notification_service.mark_all_as_read(db=db, user_id=current_user.id)
    return {"marked_count": count}


@notifications_router.post(
    "/check-triggers",
    response_model=list[NotificationResponse],
    status_code=status.HTTP_200_OK,
    summary="Evaluate goal milestones and market volatility triggers",
)
async def check_triggers(
    db: AsyncSession = Depends(get_db_session),
) -> list[NotificationResponse]:
    """Trigger background check for goal completion and major asset fluctuations (BTC, Brent Oil, etc.)."""
    notifs = await notification_service.check_triggers_and_notify(db=db)
    return [NotificationResponse.model_validate(n) for n in notifs]
