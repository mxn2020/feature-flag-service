"""Application configuration loaded from environment variables."""

from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings backed by environment variables / .env file."""

    admin_api_key: str = "change-me-admin-key"
    read_api_key: str = "change-me-read-key"
    database_url: str = "sqlite:///./feature_flags.db"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


_settings: Settings | None = None


def get_settings() -> Settings:
    """Return cached settings singleton."""
    global _settings  # noqa: PLW0603
    if _settings is None:
        _settings = Settings()
    return _settings


def reset_settings() -> None:
    """Reset settings singleton (used in tests)."""
    global _settings  # noqa: PLW0603
    _settings = None
