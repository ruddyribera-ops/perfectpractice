"""Auth endpoint tests — login, register, token structure."""
import pytest


@pytest.mark.asyncio
async def test_login_returns_valid_jwt(client):
    """
    POST /api/auth/login with student@test.com / test123 should return
    a 200 response with a valid JWT access_token.
    """
    response = await client.post(
        "/api/auth/login",
        json={"email": "student@test.com", "password": "test123"},
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()

    # Token response shape
    assert "access_token" in data, f"Missing access_token in response: {data}"
    assert "refresh_token" in data, f"Missing refresh_token in response: {data}"
    assert "user" in data, f"Missing user in response: {data}"

    access_token = data["access_token"]
    # JWT must be a non-empty string with two dots (header.payload.signature)
    assert isinstance(access_token, str), f"access_token should be string, got {type(access_token)}"
    assert access_token.count(".") == 2, f"JWT should have 3 parts, got {access_token.count('.')}: {access_token}"
    assert len(access_token) > 20, "JWT too short to be valid"

    # User shape
    user = data["user"]
    assert "id" in user, "User object missing id"
    assert "email" in user, "User object missing email"
    assert user["email"] == "student@test.com", f"Expected student@test.com, got {user['email']}"


@pytest.mark.asyncio
async def test_login_invalid_credentials_rejected(client):
    """Wrong password should return 401."""
    response = await client.post(
        "/api/auth/login",
        json={"email": "student@test.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401, f"Expected 401 for wrong password, got {response.status_code}"


@pytest.mark.asyncio
async def test_login_nonexistent_user_rejected(client):
    """Non-existent email should return 401."""
    response = await client.post(
        "/api/auth/login",
        json={"email": "nobody@example.com", "password": "test123"},
    )
    assert response.status_code == 401, f"Expected 401 for missing user, got {response.status_code}"


@pytest.mark.asyncio
async def test_protected_endpoint_without_token_rejected(client):
    """GET /api/me/stats/me without token should return 401 or 403."""
    response = await client.get("/api/me/stats/me")
    assert response.status_code in (401, 403), f"Expected 401/403 without token, got {response.status_code}"