from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Core App
    PROJECT_NAME: str = "Personal Finance Command Center"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    SECRET_KEY: str = "development-secret-key-at-least-32-chars-long"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # PostgreSQL Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/personal_fc"
    DATABASE_ECHO: bool = False
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Market Data & AI
    MARKET_DATA_PROVIDER: str = "mock"
    AI_PROVIDER: str = "mock"
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""

    # Base financial defaults
    DEFAULT_BASE_CURRENCY: str = "USD"


@lru_cache
def get_settings() -> Settings:
    return Settings()
