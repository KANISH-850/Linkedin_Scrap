"""Application configuration loaded from environment variables."""

from functools import lru_cache
from typing import List
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def normalize_database_url(url: str) -> str:
    """Normalize Postgres connection strings to use psycopg v3 driver."""
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql://") and "+psycopg" not in url:
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # App
    app_name: str = "ReferralPilot AI"
    environment: str = "development"
    debug: bool = False
    frontend_url: str = "http://localhost:5173"
    backend_url: str = "http://localhost:8000"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # Security
    secret_key: str = "change-me-to-a-long-random-secret-key-in-production"
    access_token_expire_minutes: int = 1440
    admin_email: str = "admin@referralpilot.app"
    admin_password: str = "ChangeMeStrongPassword123!"

    # Database
    database_url: str = "sqlite+pysqlite:///./referralpilot_dev.db"

    # AI / LLM
    llm_provider: str = "heuristic"  # openai | gemini | heuristic
    llm_api_key: str = ""
    llm_base_URL: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o-mini"
    llm_timeout_seconds: int = 30

    # Telegram
    telegram_bot_token: str = ""
    telegram_authorized_user_id: str = ""
    telegram_webhook_secret: str = "change-me-telegram-webhook-secret"

    # Discovery & Scheduler
    scheduler_timezone: str = "Asia/Kolkata"
    discovery_request_timeout_seconds: int = 15
    discovery_max_items_per_source: int = 25
    high_match_threshold: int = 75
    cron_api_secret: str = "change-me-cron-shared-secret"

    @field_validator("database_url", mode="before")
    @classmethod
    def _normalize_db(cls, v: str) -> str:
        return normalize_database_url(v)

    @property
    def cors_origin_list(self) -> List[str]:
        origins = [o.strip() for o in self.cors_origins.split(",") if o.strip()]
        if self.frontend_url and self.frontend_url not in origins:
            origins.append(self.frontend_url)
        return origins

    def validate_production_constraints(self) -> None:
        """Enforce production security and database requirements."""
        if self.environment.lower() == "production":
            if self.database_url.startswith("sqlite"):
                raise RuntimeError(
                    "SQLite is not permitted in production. Configure DATABASE_URL for Supabase PostgreSQL."
                )
            if "change-me" in self.secret_key or len(self.secret_key) < 32:
                raise RuntimeError(
                    "SECRET_KEY must be set to a secure random string (>= 32 chars) in production."
                )


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
