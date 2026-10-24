import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # NOTE (fixed 2026-10-25): this class previously read only process env vars,
    # so a key put in backend/.env was silently ignored. model_config below makes
    # pydantic-settings actually load backend/.env (when uvicorn runs from backend/).
    # Process env vars still win over .env values.
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    groq_api_key: str | None = None
    groq_model: str = "llama-3.3-70b-versatile"
    # PostgreSQL is the intended primary DB. SQLite is only the local fallback
    # when DATABASE_URL is not set (e.g. no Docker/Postgres in this sandbox).
    database_url: str = "sqlite:///./aivoa.db"
    max_upload_mb: int = 10
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def db_kind(self) -> str:
        return "postgresql" if self.database_url.startswith(("postgresql", "postgres")) else "sqlite"

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
