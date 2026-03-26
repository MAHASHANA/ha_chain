"""Application configuration loaded from environment variables."""

from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central settings object populated via ``.env`` or environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # --- Database -----------------------------------------------------------
    DATABASE_URL: str = (
        "postgresql+asyncpg://hachain:hachain@localhost:5432/hachain"
    )
    DATABASE_ECHO: bool = False

    # --- Redis / Celery -----------------------------------------------------
    REDIS_URL: str = "redis://localhost:6379/0"

    # --- Stellar ------------------------------------------------------------
    STELLAR_NETWORK: str = "testnet"
    STELLAR_SECRET_KEY: str = ""
    STELLAR_HORIZON_URL: str = "https://horizon-testnet.stellar.org"

    # --- JWT ----------------------------------------------------------------
    JWT_SECRET: str = "change-me-to-a-random-secret-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # --- Compliance APIs ----------------------------------------------------
    CHAINALYSIS_API_KEY: str = ""
    ELLIPTIC_API_KEY: str = ""

    # --- Application --------------------------------------------------------
    APP_NAME: str = "HaChain"
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    CORS_ORIGINS: List[str] = Field(default=["http://localhost:3000"])

    # --- Transfer limits ----------------------------------------------------
    QUOTE_EXPIRY_MINUTES: int = 15
    AGENT_ACCEPT_TIMEOUT_MINUTES: int = 5
    MAX_DAILY_TRANSFER_KYC1: float = 1000.0
    MAX_DAILY_TRANSFER_KYC2: float = 5000.0
    MAX_DAILY_TRANSFER_KYC3: float = 50000.0

    # --- Compliance thresholds ----------------------------------------------
    ENHANCED_REVIEW_THRESHOLD: float = 3000.0
    VELOCITY_24H_THRESHOLD: float = 10000.0
    STRUCTURING_WINDOW_HOURS: int = 48
    STRUCTURING_AMOUNT_THRESHOLD: float = 3000.0
    STRUCTURING_COUNT_THRESHOLD: int = 3


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached singleton of the application settings."""
    return Settings()


# Module-level convenience alias used by services that do ``from app.config import settings``
settings = get_settings()
