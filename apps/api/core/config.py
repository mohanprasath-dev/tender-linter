from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment or .env file."""

    APP_NAME: str = "Tender Linter API"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "dev"

    # Database configuration (SQLite for dev, PostgreSQL for production/docker)
    DATABASE_URL: str = "sqlite:///./dev.sqlite"

    # Storage and provider configuration
    OBJECT_STORE_PATH: str = "./object_store"
    PROVIDER_PRIMARY: str | None = None
    PROVIDER_SECONDARY: str | None = None
    MODEL_ID_PRIMARY: str | None = None
    MODEL_ID_SECONDARY: str | None = None
    PROVIDER_PRIMARY_KEY: str | None = None
    PROVIDER_SECONDARY_KEY: str | None = None
    RATE_LIMIT_RPM: int | None = None
    DAILY_CAP: int | None = None
    STALE_DAYS: int | None = None
    RETENTION_DAYS: int | None = None
    JWT_SECRET: str = "dev_secret_key_change_in_production"
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"
    LOG_LEVEL: str = "info"

    # Repository root directory
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent.parent

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]


settings = Settings()
