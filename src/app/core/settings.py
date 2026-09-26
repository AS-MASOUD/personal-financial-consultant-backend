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

    # Communications & OTP (Supports Iranian SMS & Email Providers)
    SMS_PROVIDER: str = "mock"  # mock, kavenegar, farazsms
    KAVENEGAR_API_KEY: str = ""
    KAVENEGAR_SENDER: str = ""
    FARAZSMS_API_KEY: str = ""
    FARAZSMS_SENDER: str = ""
    FARAZSMS_PATTERN_CODE: str = ""

    EMAIL_PROVIDER: str = "mock"  # mock, smtp
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "no-reply@personal-fc.local"
    SMTP_USE_TLS: bool = True

    OTP_EXPIRE_SECONDS: int = 120
    OTP_COOLDOWN_SECONDS: int = 60
    OTP_DIGITS: int = 5

    # Asset Volatility Alert Threshold (%)
    ASSET_ALERT_THRESHOLD_PERCENT: float = 4.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
