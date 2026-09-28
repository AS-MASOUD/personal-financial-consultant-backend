from decimal import Decimal
from typing import Any

import httpx

from src.app.core.settings import get_settings
from src.app.observability.logging import get_logger

logger = get_logger("assets.market_data_client")
settings = get_settings()


class MarketDataClient:
    """HTTP Client for BRS Market Data APIs.

    Fetches Commodities, Cryptocurrencies, Gold & Forex rates.
    """

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.BRS_API_KEY
        self.timeout = 15.0

    async def fetch_commodities(self) -> dict[str, list[dict[str, Any]]]:
        """Fetch precious metals (Gold, Silver, Platinum), base metals (Copper, Aluminum), and energy."""
        url = f"{settings.BRS_COMMODITY_URL}?key={self.api_key}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.json()
                if isinstance(data, dict):
                    return data
                logger.warning("Unexpected response format from Commodity API: %s", data)
                return {}
        except Exception as e:
            logger.error("Failed to fetch commodities from BRS API: %s", str(e))
            return {}

    async def fetch_cryptocurrency(self) -> list[dict[str, Any]]:
        """Fetch live cryptocurrency prices (USD and Toman)."""
        url = f"{settings.BRS_CRYPTO_URL}?key={self.api_key}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.json()
                if isinstance(data, list):
                    return data
                logger.warning("Unexpected response format from Crypto API: %s", data)
                return []
        except Exception as e:
            logger.error("Failed to fetch cryptocurrencies from BRS API: %s", str(e))
            return []

    async def fetch_gold_and_currency(self) -> dict[str, list[dict[str, Any]]]:
        """Fetch Iranian domestic gold (18K, 24K, melted, coins) and foreign currencies (USD, EUR, etc.)."""
        url = f"{settings.BRS_GOLD_CURRENCY_URL}?key={self.api_key}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.json()
                if isinstance(data, dict):
                    return data
                logger.warning("Unexpected response format from Gold & Currency API: %s", data)
                return {}
        except Exception as e:
            logger.error("Failed to fetch gold and currencies from BRS API: %s", str(e))
            return {}
