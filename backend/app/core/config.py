from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@postgres:5432/math_platform"
    REDIS_URL: str = "redis://redis:6379"
    JWT_SECRET: str = "dev-secret-change-in-prod-min-32-chars!!"
    JWT_REFRESH_SECRET: str = "dev-refresh-secret-change-in-prod-min-32!"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Google Classroom OAuth 2.0
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:3000/api/classroom/callback"

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
