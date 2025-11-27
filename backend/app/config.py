"""Configuration from environment variables."""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pathlib import Path


# Get base directory (backend folder)
BASE_DIR = Path(__file__).resolve().parent.parent
# Project root (one level up from backend)
PROJECT_ROOT = BASE_DIR.parent


class Settings(BaseSettings):
    """Application settings."""

    # AI Provider (required)
    AI_BASE_URL: str = ""
    AI_API_KEY: str = ""
    AI_MODEL: str = "gpt-4o-mini"
    AI_TEMPERATURE: float = 0.7
    AI_MAX_TOKENS: int = 1000

    # GigaChat specific (for auto token refresh)
    GIGACHAT_CREDENTIALS: Optional[str] = None

    # Storage
    STORAGE_TYPE: str = "json"  # json, sqlite, postgres
    DATABASE_URL: Optional[str] = None

    # Telegram Alerts (optional)
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[str] = None

    # Server
    PORT: int = 8080
    DEBUG: bool = False
    CORS_ORIGINS: str = "*"

    # Paths (can be overridden via env for Docker)
    KNOWLEDGE_PATH: Optional[str] = None
    DATA_PATH: Optional[str] = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Set paths after initialization
        # In Docker: /app/knowledge, /app/data
        # Local: project_root/knowledge, project_root/data
        if not self.KNOWLEDGE_PATH:
            # Check if running in Docker (backend/app is at /app/app)
            if BASE_DIR == Path("/app"):
                self.KNOWLEDGE_PATH = "/app/knowledge"
            else:
                self.KNOWLEDGE_PATH = str(PROJECT_ROOT / "knowledge")
        if not self.DATA_PATH:
            if BASE_DIR == Path("/app"):
                self.DATA_PATH = "/app/data"
            else:
                self.DATA_PATH = str(PROJECT_ROOT / "data")

    class Config:
        env_file = str(BASE_DIR / ".env")  # Use absolute path
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields in .env


settings = Settings()


def validate_settings():
    """Validate required settings."""
    errors = []

    if not settings.AI_BASE_URL:
        errors.append("AI_BASE_URL is required")
    if not settings.AI_API_KEY:
        errors.append("AI_API_KEY is required")

    if settings.STORAGE_TYPE == "postgres" and not settings.DATABASE_URL:
        errors.append("DATABASE_URL is required for postgres storage")

    if errors:
        raise ValueError("Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors))
