"""Authenticated /api/me endpoint tests."""
import pytest


async def _login_get_token(client):
    """Helper: login as student@test.com and return the access token."""
    response = await client.post(
        "/api/auth/login",
        json={"email": "student@test.com", "password": "test123"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.mark.asyncio
async def test_me_stats_me_with_valid_jwt(client):
    """
    GET /api/me/stats/me with a valid JWT should return 200
    and a user-stats payload (total_xp, level, etc.).
    """
    token = await _login_get_token(client)

    response = await client.get(
        "/api/me/stats/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()

    # Expected fields from StatsResponse
    assert "total_xp" in data, f"Missing total_xp: {data}"
    assert "level" in data, f"Missing level: {data}"
    assert "points" in data, f"Missing points: {data}"
    assert "current_streak" in data, f"Missing current_streak: {data}"
    assert isinstance(data["total_xp"], int), f"total_xp should be int, got {type(data['total_xp'])}"
    assert isinstance(data["level"], int), f"level should be int, got {type(data['level'])}"


@pytest.mark.asyncio
async def test_me_progress_with_valid_jwt(client):
    """
    GET /api/me/progress with a valid JWT should return 200 and a list.
    """
    token = await _login_get_token(client)

    response = await client.get(
        "/api/me/progress",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert isinstance(data, list), f"progress should return a list, got {type(data)}"


@pytest.mark.asyncio
async def test_me_stats_me_with_bogus_token_rejected(client):
    """Invalid JWT should return 401."""
    response = await client.get(
        "/api/me/stats/me",
        headers={"Authorization": "Bearer not.a.valid.token.at.all"},
    )
    assert response.status_code == 401, f"Expected 401 for bogus token, got {response.status_code}"


@pytest.mark.asyncio
async def test_me_stats_me_without_token_rejected(client):
    """No Authorization header should return 401."""
    response = await client.get("/api/me/stats/me")
    assert response.status_code in (401, 403), f"Expected 401/403 without token, got {response.status_code}"