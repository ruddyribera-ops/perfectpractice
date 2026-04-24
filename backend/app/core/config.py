import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow",
    )

    DATABASE_URL: str = os.environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/math_platform",
    )
    REDIS_URL: str = os.environ.get("REDIS_URL", "redis://redis:6379")
    JWT_SECRET: str = os.environ.get("JWT_SECRET", "dev-secret-change-in-prod-min-32-chars!!")
    JWT_REFRESH_SECRET: str = os.environ.get("JWT_REFRESH_SECRET", "dev-refresh-secret-change-in-prod-min-32!")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:3000/api/classroom/callback"


settings = Settings()
