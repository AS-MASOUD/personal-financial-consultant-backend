import asyncio
from datetime import UTC, datetime

from src.app.core.settings import get_settings
from src.app.database.session import AsyncSessionFactory
from src.app.observability.logging import get_logger
from src.modules.assets.application.dtos import MarketSyncResultResponse
from src.modules.assets.application.market_sync_service import MarketSyncService

logger = get_logger("assets.scheduler")
settings = get_settings()


class MarketPriceScheduler:
    """Background task runner to periodically update market prices.

    Executes ~5 times a day to avoid hitting external API rate limits.
    All users read from the local DB and in-memory cache without triggering external API calls.
    """

    def __init__(self):
        self.service = MarketSyncService()
        self._task: asyncio.Task | None = None
        self._stop_event = asyncio.Event()
        self._last_manual_sync: datetime | None = None
        self._manual_cooldown_seconds = 60

    async def start(self) -> None:
        """Start the background sync loop task."""
        if not settings.ENABLE_MARKET_SYNC_TASK:
            logger.info("Market price background sync task is disabled in settings.")
            return

        if self._task and not self._task.done():
            logger.warning("Market price scheduler task is already running.")
            return

        self._stop_event.clear()
        self._task = asyncio.create_task(self._run_loop(), name="market_price_sync_loop")
        logger.info(
            "Market price scheduler task started. Interval: %.1f hours (~%d times per day).",
            settings.MARKET_SYNC_INTERVAL_HOURS,
            round(24.0 / settings.MARKET_SYNC_INTERVAL_HOURS),
        )

    async def stop(self) -> None:
        """Stop the background sync loop task."""
        self._stop_event.set()
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            logger.info("Market price scheduler task stopped cleanly.")

    async def _run_loop(self) -> None:
        """Main periodic loop."""
        # Initial delay after boot to let DB and web server settle
        try:
            await asyncio.sleep(5)
        except asyncio.CancelledError:
            return

        interval_seconds = int(settings.MARKET_SYNC_INTERVAL_HOURS * 3600)

        while not self._stop_event.is_set():
            try:
                logger.info("Scheduled market sync triggered by background worker.")
                async with AsyncSessionFactory() as db:
                    await self.service.sync_market_prices(db)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error during scheduled market sync: %s", str(e), exc_info=True)

            try:
                # Wait for interval or until stopped
                await asyncio.wait_for(self._stop_event.wait(), timeout=interval_seconds)
            except TimeoutError:
                continue
            except asyncio.CancelledError:
                break

    async def trigger_manual_sync(self) -> MarketSyncResultResponse:
        """Trigger an on-demand synchronization with a cooldown to protect external API rate limits."""
        now = datetime.now(UTC)
        if self._last_manual_sync:
            elapsed = (now - self._last_manual_sync).total_seconds()
            if elapsed < self._manual_cooldown_seconds:
                wait_sec = int(self._manual_cooldown_seconds - elapsed)
                cached = await self.service.get_market_rates()
                return MarketSyncResultResponse(
                    success=True,
                    message=f"نرخ‌ها به تازگی بروزرسانی شده‌اند. لطفاً {wait_sec} ثانیه دیگر مجدداً تلاش فرمایید.",
                    updated_assets_count=0,
                    total_quotes_fetched=len(cached.gold_and_coins) + len(cached.commodities) + len(cached.currencies) + len(cached.cryptocurrency),
                    last_sync_time=cached.last_sync_time or now,
                )

        async with AsyncSessionFactory() as db:
            result = await self.service.sync_market_prices(db)
            self._last_manual_sync = now
            return result


# Global singleton instance
market_scheduler = MarketPriceScheduler()
