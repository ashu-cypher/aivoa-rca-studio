import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    groq_api_key: str | None = os.getenv("GROQ_API_KEY")
    groq_model: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    # PostgreSQL is the intended primary DB. SQLite is only the local fallback
    # when DATABASE_URL is not set (e.g. no Docker/Postgres in this sandbox).
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./aivoa.db")
    max_upload_mb: int = 10
    cors_origins: str = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")

    @property
    def db_kind(self) -> str:
        return "postgresql" if self.database_url.startswith(("postgresql", "postgres")) else "sqlite"

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
