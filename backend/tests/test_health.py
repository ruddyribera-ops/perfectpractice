"""Health endpoint tests."""
import pytest


@pytest.mark.asyncio
async def test_health_returns_200(client):
    """GET /api/health should return 200 and healthy status."""
    response = await client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


@pytest.mark.asyncio
async def test_root_health(client):
    """GET /health should also return 200."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"