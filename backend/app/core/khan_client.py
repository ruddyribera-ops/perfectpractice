"""
Khan Academy API client.
Wired for future API access — currently returns empty structured data.
Activates when Khan Academy opens public API access.
"""

import httpx
from typing import Any


class KhanAcademyClient:
    """
    Khan Academy API client.

    Currently returns empty structured results.
    When Khan Academy opens their API, set the API key via constructor
    and the methods below will return real data.
    """

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or ""
        self._base_url = "https://www.khanacademy.org/api/v1"

    @property
    def _auth_headers(self) -> dict[str, str]:
        if self.api_key:
            return {"Authorization": f"Key {self.api_key}"}
        return {}

    async def _get(self, path: str) -> list[dict[str, Any]]:
        """Make an authenticated GET request to Khan Academy API."""
        if not self.api_key:
            return []

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self._base_url}{path}",
                    headers=self._auth_headers,
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()
                return data if isinstance(data, list) else [data]
            except Exception:
                return []

    # -------------------------------------------------------------------------
    # Content access methods (activated when api_key is set)
    # -------------------------------------------------------------------------

    async def get_courses(self) -> list[dict[str, Any]]:
        """
        Return list of available courses/topics.
        Structure: [{ka_id, title, description, subject, grade_levels}]
        """
        return []

    async def get_topics(self, course_id: str) -> list[dict[str, Any]]:
        """
        Return subtopics/units within a course.
        Structure: [{ka_id, title, description, order}]
        """
        return []

    async def get_lessons(self, topic_id: str) -> list[dict[str, Any]]:
        """
        Return lessons/articles within a topic.
        Structure: [{ka_id, title, content, content_type, order}]
        """
        return []

    async def get_exercises(self, topic_id: str) -> list[dict[str, Any]]:
        """
        Return practice exercises for a topic.
        Structure: [{
            ka_id, title, exercise_type, difficulty,
            data: {question, choices, correct_answer, explanation},
            hints
        }]
        """
        return []

    async def search_content(self, query: str) -> list[dict[str, Any]]:
        """
        Search Khan Academy content by keyword.
        Returns: [{ka_id, title, type, description}]
        """
        return []

    # -------------------------------------------------------------------------
    # Import transformer helpers
    # -------------------------------------------------------------------------

    def transform_course(self, course: dict[str, Any]) -> dict[str, Any] | None:
        """
        Transform Khan Academy course data to our Topic schema.
        Returns dict with: slug, title, description, icon_name (empty for now)
        """
        return None

    def transform_topic(self, topic: dict[str, Any]) -> dict[str, Any] | None:
        """
        Transform Khan Academy topic/unit to our Unit schema.
        Returns dict with: slug, title, description, order_index
        """
        return None

    def transform_exercise(self, exercise: dict[str, Any]) -> dict[str, Any] | None:
        """
        Transform Khan Academy exercise to our Exercise schema.
        Returns dict with: slug, title, exercise_type, difficulty,
                          points_value, data, hints
        """
        return None

    def transform_lesson(self, lesson: dict[str, Any]) -> dict[str, Any] | None:
        """
        Transform Khan Academy lesson/article to our Lesson schema.
        Returns dict with: title, content, content_type, order_index
        """
        return None