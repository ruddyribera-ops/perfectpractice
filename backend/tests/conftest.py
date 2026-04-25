"""
Pytest configuration and shared fixtures for backend tests.
"""
import pytest
import pytest_asyncio
import os
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# Override DATABASE_URL before importing the app
os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:zMMxobzDtVMtpViNLeYCAGgGxUSZUjSz@shortline.proxy.rlwy.net:19435/railway"

from app.main import app
from app.core.database import Base


@pytest_asyncio.fixture(scope="session")
async def engine():
    """Create a shared async engine for the test session."""
    from app.core.config import settings
    eng = create_async_engine(settings.DATABASE_URL, echo=False)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture(scope="session")
async def db_session(engine):
    """Provide a single session for the whole test session (tables created once)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session


@pytest_asyncio.fixture
async def client():
    """Async HTTP client pointed at the FastAPI app."""
    test_url = "postgresql+asyncpg://postgres:zMMxobzDtVMtpViNLeYCAGgGxUSZUjSz@shortline.proxy.rlwy.net:19435/railway"
    from sqlalchemy.ext.asyncio import create_async_engine
    from app.core.database import get_db
    test_engine = create_async_engine(test_url, echo=False)
    try:
        async def override_get_db():
            from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
            session_maker = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
            async with session_maker() as session:
                yield session

        app.dependency_overrides[get_db] = override_get_db
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
        app.dependency_overrides.clear()
    finally:
        await test_engine.dispose()