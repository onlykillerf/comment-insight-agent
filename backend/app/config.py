from __future__ import annotations

from functools import lru_cache
from pathlib import Path

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
except Exception:  # pragma: no cover - fallback for older local setups
    from pydantic import BaseSettings  # type: ignore
    SettingsConfigDict = dict  # type: ignore


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    app_name: str = "Cross-Platform Comment Insight Agent"
    environment: str = "local"
    database_url: str = "sqlite:///./comment_insight.db"
    redis_url: str = "redis://localhost:6379/0"
    qdrant_url: str = "http://localhost:6333"
    llm_provider: str = "mock"
    llm_model: str | None = None
    llm_base_url: str | None = None
    openai_api_key: str | None = None
    deepseek_api_key: str | None = None
    qwen_api_key: str | None = None
    siliconflow_api_key: str | None = None
    media_crawler_path: str | None = None

    model_config = SettingsConfigDict(
        env_file=(".env", PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""

    return Settings()
