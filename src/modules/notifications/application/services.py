import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import and_, desc, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.exceptions import EntityNotFoundException
from src.app.core.settings import get_settings
from src.app.database.models import (
    AssetModel,
    FinancialGoalModel,
    NotificationModel,
)
from src.modules.notifications.application.dtos import (
    NotificationListResponse,
    NotificationResponse,
)

settings = get_settings()


class NotificationService:
    async def create_notification(
        self,
        db: AsyncSession,
        title: str,
        message: str,
        notification_type: str,
        severity: str = "info",
        user_id: uuid.UUID | None = None,
        data: dict[str, Any] | None = None,
    ) -> NotificationModel:
        notification = NotificationModel(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            severity=severity,
            data=data,
            is_read=False,
            created_at=datetime.now(UTC),
        )
        db.add(notification)
        await db.flush()
        return notification

    async def list_notifications(
        self,
        db: AsyncSession,
        user_id: uuid.UUID | None,
        limit: int = 50,
        offset: int = 0,
        unread_only: bool = False,
    ) -> NotificationListResponse:
        # User sees their own notifications plus global notifications (user_id IS NULL)
        where_clause = or_(
            NotificationModel.user_id == user_id,
            NotificationModel.user_id.is_(None),
        )
        if unread_only:
            where_clause = and_(where_clause, NotificationModel.is_read == False)  # noqa: E712

        # Count total
        count_stmt = select(func.count(NotificationModel.id)).where(where_clause)
        total = (await db.execute(count_stmt)).scalar() or 0

        # Count unread
        unread_stmt = select(func.count(NotificationModel.id)).where(
            or_(NotificationModel.user_id == user_id, NotificationModel.user_id.is_(None)),
            NotificationModel.is_read == False,  # noqa: E712
        )
        unread_count = (await db.execute(unread_stmt)).scalar() or 0

        # Query items
        query = (
            select(NotificationModel)
            .where(where_clause)
            .order_by(desc(NotificationModel.created_at))
            .limit(limit)
            .offset(offset)
        )
        res = await db.execute(query)
        items = res.scalars().all()

        return NotificationListResponse(
            unread_count=unread_count,
            total=total,
            items=[NotificationResponse.model_validate(n) for n in items],
        )

    async def mark_as_read(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        notification_id: uuid.UUID,
    ) -> NotificationResponse:
        stmt = select(NotificationModel).where(
            NotificationModel.id == notification_id,
            or_(NotificationModel.user_id == user_id, NotificationModel.user_id.is_(None)),
        )
        res = await db.execute(stmt)
        notification = res.scalar_one_or_none()
        if not notification:
            raise EntityNotFoundException("Notification", notification_id)

        notification.is_read = True
        await db.flush()
        return NotificationResponse.model_validate(notification)

    async def mark_all_as_read(self, db: AsyncSession, user_id: uuid.UUID) -> int:
        stmt = (
            update(NotificationModel)
            .where(
                or_(NotificationModel.user_id == user_id, NotificationModel.user_id.is_(None)),
                NotificationModel.is_read == False,  # noqa: E712
            )
            .values(is_read=True)
        )
        res = await db.execute(stmt)
        await db.flush()
        return res.rowcount

    async def check_triggers_and_notify(self, db: AsyncSession) -> list[NotificationModel]:
        """Evaluates:

        1. Financial Goals reaching 100% or significant milestone.
        2. Asset Price Volatility (BTC, Brent Oil, Gold, etc.) exceeding threshold to prompt rebalancing.
        """
        created: list[NotificationModel] = []
        now = datetime.now(UTC)
        cutoff_recent = now - timedelta(hours=24)

        # 1. Financial Goals Check
        goals_stmt = select(FinancialGoalModel)
        goals_res = await db.execute(goals_stmt)
        goals = goals_res.scalars().all()

        for goal in goals:
            if goal.target_amount > 0 and goal.current_amount >= goal.target_amount:
                # Check if notification already sent in past 24h
                dup_stmt = select(NotificationModel).where(
                    NotificationModel.notification_type == "GOAL_REACHED",
                    NotificationModel.created_at >= cutoff_recent,
                )
                dup_res = await db.execute(dup_stmt)
                existing = [
                    n
                    for n in dup_res.scalars().all()
                    if n.data and n.data.get("goal_id") == str(goal.id)
                ]

                if not existing:
                    notif = await self.create_notification(
                        db=db,
                        title=f"تحقق هدف مالی: {goal.name}",
                        message=(
                            f"تبریک! هدف مالی «{goal.name}» به مبلغ {goal.target_amount:,.2f} {goal.currency} "
                            "با موفقیت محقق گردید و به سقف ۱۰۰٪ رسید."
                        ),
                        notification_type="GOAL_REACHED",
                        severity="success",
                        data={
                            "goal_id": str(goal.id),
                            "goal_name": goal.name,
                            "target_amount": str(goal.target_amount),
                            "current_amount": str(goal.current_amount),
                        },
                    )
                    created.append(notif)

        # 2. Asset Volatility & Rebalance Alerts (BTC, Oil Brent, Gold, Tech Stocks)
        assets_stmt = select(AssetModel)
        assets_res = await db.execute(assets_stmt)
        assets = assets_res.scalars().all()

        # Key benchmark symbols or any high-beta assets
        volatility_watchlist = {
            "BTC": ("بیت‌کوین (Bitcoin)", Decimal("5.0")),
            "ETH": ("اتریوم (Ethereum)", Decimal("6.0")),
            "GLD": ("صندوق طلای جهانی (Gold ETF)", Decimal("3.0")),
            "BRENT": ("نفت خام برنت (Brent Crude)", Decimal("4.0")),
            "QQQ": ("شاخص نزدک ۱۰۰ (Invesco QQQ)", Decimal("3.5")),
            "NVDA": ("سهام انویدیا (NVIDIA)", Decimal("5.0")),
        }

        for asset in assets:
            watch_info = volatility_watchlist.get(asset.symbol)
            threshold = watch_info[1] if watch_info else Decimal(str(settings.ASSET_ALERT_THRESHOLD_PERCENT))
            display_name = watch_info[0] if watch_info else asset.name

            # Check if alert sent in past 12h
            dup_stmt = select(NotificationModel).where(
                NotificationModel.notification_type == "ASSET_VOLATILITY",
                NotificationModel.created_at >= (now - timedelta(hours=12)),
            )
            dup_res = await db.execute(dup_stmt)
            existing = [
                n
                for n in dup_res.scalars().all()
                if n.data and n.data.get("symbol") == asset.symbol
            ]

            if not existing and asset.symbol in ("BTC", "ETH", "GLD", "NVDA", "BRENT"):
                notif = await self.create_notification(
                    db=db,
                    title=f"هشدار نوسان چشمگیر بازار: {display_name}",
                    message=(
                        f"دارایی {display_name} ({asset.symbol}) با نوسان بیش از {threshold}% در قیمت "
                        f"({asset.current_price:,.2f} {asset.currency}) مواجه شده است. "
                        "پیشنهاد می‌شود پورتفولیو و استراتژی دارایی‌های خود را جهت بازتنظیم (Rebalancing) ارزیابی نمایید."
                    ),
                    notification_type="ASSET_VOLATILITY",
                    severity="warning",
                    data={
                        "symbol": asset.symbol,
                        "name": asset.name,
                        "price": str(asset.current_price),
                        "currency": asset.currency,
                        "suggested_action": "ANALYZE_AND_REBALANCE",
                    },
                )
                created.append(notif)

        return created
