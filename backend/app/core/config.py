import os
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow",
    )

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/railway"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def force_railway_db(cls, v: str) -> str:
        # Only force /railway when RAILWAY_ENVIRONMENT is set ( Railway production )
        if os.environ.get("RAILWAY_ENVIRONMENT"):
            return v.rsplit("/", 1)[0] + "/railway"
        return v
    REDIS_URL: str = os.environ.get("REDIS_URL", "redis://redis:6379")
    JWT_SECRET: str = os.environ.get("JWT_SECRET", "dev-secret-change-in-prod-min-32-chars!!")
    JWT_REFRESH_SECRET: str = os.environ.get("JWT_REFRESH_SECRET", "dev-refresh-secret-change-in-prod-min-32!")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:3000/api/classroom/callback"

    FRONTEND_URL: str = "http://localhost:3000"
    RAILWAY_FRONTEND_URL: str = "https://proactive-wisdom-production-cd0e.up.railway.app"


settings = Settings()
