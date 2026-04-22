"""
Google Classroom OAuth 2.0 + API client.
Handles token management, OAuth flow, and Classroom API calls.
"""

import httpx
from datetime import datetime, timezone, timedelta
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.models.classroom_sync import ClassroomSync


class GoogleClassroomClient:
    """Google Classroom API client with automatic token refresh."""

    def __init__(
        self,
        access_token: str,
        refresh_token: str,
        token_expires_at: datetime,
        db: AsyncSession | None = None,
        sync_record: ClassroomSync | None = None,
    ):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.token_expires_at = token_expires_at
        self._db = db
        self._sync_record = sync_record

    # -------------------------------------------------------------------------
    # Token management
    # -------------------------------------------------------------------------

    async def _refresh_if_needed(self) -> str:
        """Return a valid access token, refreshing if expired."""
        if self.token_expires_at <= datetime.now(timezone.utc) - timedelta(minutes=5):
            await self._do_refresh()
        return self.access_token

    async def _do_refresh(self) -> None:
        """Exchange refresh token for new access token."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "refresh_token": self.refresh_token,
                    "grant_type": "refresh_token",
                },
            )
            response.raise_for_status()
            data = response.json()
            self.access_token = data["access_token"]
            self.token_expires_at = datetime.now(timezone.utc) + timedelta(
                seconds=data.get("expires_in", 3600)
            )

        # Persist new token to DB if we have a sync record
        if self._sync_record and self._db:
            self._sync_record.access_token = self.access_token
            self._sync_record.token_expires_at = self.token_expires_at
            self._db.add(self._sync_record)
            await self._db.commit()

    # -------------------------------------------------------------------------
    # HTTP helper
    # -------------------------------------------------------------------------

    async def _get(self, url: str) -> dict[str, Any]:
        token = await self._refresh_if_needed()
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers={"Authorization": f"Bearer {token}"},
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()

    async def _post(self, url: str, json: dict[str, Any] | None = None) -> dict[str, Any]:
        token = await self._refresh_if_needed()
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=json,
                headers={"Authorization": f"Bearer {token}"},
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()

    # -------------------------------------------------------------------------
    # Classroom API methods
    # -------------------------------------------------------------------------

    async def list_courses(self) -> list[dict[str, Any]]:
        """Return all courses the teacher owns."""
        data = await self._get(
            "https://classroom.googleapis.com/v1/courses?courseStates=ACTIVE"
        )
        return data.get("courses", [])

    async def get_course(self, course_id: str) -> dict[str, Any]:
        return await self._get(f"https://classroom.googleapis.com/v1/courses/{course_id}")

    async def list_topics(self, course_id: str) -> list[dict[str, Any]]:
        """Return topics for a given course."""
        data = await self._get(
            f"https://classroom.googleapis.com/v1/courses/{course_id}/topics"
        )
        return data.get("topics", [])

    async def create_topic(self, course_id: str, name: str) -> dict[str, Any]:
        """Create a topic in a Classroom course. Returns the created topic."""
        return await self._post(
            f"https://classroom.googleapis.com/v1/courses/{course_id}/topics",
            json={"name": name},
        )

    async def list_course_work(self, course_id: str) -> list[dict[str, Any]]:
        """Return course work (assignments) for a course."""
        data = await self._get(
            f"https://classroom.googleapis.com/v1/courses/{course_id}/courseWork"
        )
        return data.get("courseWork", [])

    async def create_course_work(
        self,
        course_id: str,
        title: str,
        description: str | None = None,
        due_date: str | None = None,
    ) -> dict[str, Any]:
        """
        Create an assignment in Google Classroom.

        due_date format: "2026-06-15" (YYYY-MM-DD)
        Returns the created courseWork resource.
        """
        body: dict[str, Any] = {
            "title": title,
            "state": "PUBLISHED",
        }
        if description:
            body["description"] = description
        if due_date:
            body["dueDate"] = {
                "year": int(due_date[:4]),
                "month": int(due_date[5:7]),
                "day": int(due_date[8:10]),
            }
            body["dueTime"] = {"hours": 23, "minutes": 59}

        return await self._post(
            f"https://classroom.googleapis.com/v1/courses/{course_id}/courseWork",
            json=body,
        )

    async def list_students(self, course_id: str) -> list[dict[str, Any]]:
        """Return student list for a course."""
        data = await self._get(
            f"https://classroom.googleapis.com/v1/courses/{course_id}/students"
        )
        return data.get("students", [])

    async def list_teachers(self, course_id: str) -> list[dict[str, Any]]:
        """Return teacher list for a course."""
        data = await self._get(
            f"https://classroom.googleapis.com/v1/courses/{course_id}/teachers"
        )
        return data.get("teachers", [])


# =============================================================================
# OAuth helpers (used by router)
# =============================================================================


def build_google_oauth_url(state: str) -> str:
    """Build the Google OAuth authorization URL."""
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": (
            "openid email "
            "https://www.googleapis.com/auth/classroom.courses "
            "https://www.googleapis.com/auth/classroom.coursework.students "
            "https://www.googleapis.com/auth/classroom.topics "
            "https://www.googleapis.com/auth/classroom.rosters"
        ),
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    qs = "&".join(f"{k}={v}" for k, v in params.items())
    return f"https://accounts.google.com/o/oauth2/v2/auth?{qs}"


async def exchange_code_for_tokens(code: str) -> dict[str, Any]:
    """Exchange authorization code for access + refresh tokens."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            },
        )
        response.raise_for_status()
        return response.json()


async def get_oauth_token_info(access_token: str) -> dict[str, Any]:
    """Validate an access token and return user info."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://oauth2.googleapis.com/tokeninfo",
            params={"access_token": access_token},
        )
        response.raise_for_status()
        return response.json()