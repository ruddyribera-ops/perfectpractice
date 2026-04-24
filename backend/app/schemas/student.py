from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional, Any


class ProgressResponse(BaseModel):
    topic_id: int
    topic_title: str
    exercises_completed: int
    total_exercises: int
    mastery_score: float


class AttemptRequest(BaseModel):
    answer: Any
    time_spent_seconds: int = 0
    assignment_id: Optional[int] = None
    helped_peer_id: Optional[int] = None


class AchievementResponse(BaseModel):
    id: int
    badge_key: str
    title: str
    description: Optional[str]
    icon: Optional[str]
    earned_at: datetime
    class Config:
        from_attributes = True


class AttemptResponse(BaseModel):
    correct: bool
    points_earned: int
    xp_earned: int
    explanation: Optional[str]
    new_mastery: float
    streak_updated: bool
    current_streak: int
    new_achievements: list[AchievementResponse] = []


class StreakResponse(BaseModel):
    current_streak: int
    longest_streak: int
    last_activity_date: Optional[date]
    streak_freeze_available: int
    streak_at_risk: bool


class StatsResponse(BaseModel):
    total_xp: int
    level: int
    points: int
    current_streak: int
    longest_streak: int
    exercises_completed: int
    lessons_completed: int
    xp_to_next_level: int


class StreakFreezeResponse(BaseModel):
    success: bool
    message: str
    freezes_remaining: int
    new_achievements: list[AchievementResponse] = []


class AttemptHistoryItem(BaseModel):
    id: int
    assignment_id: int | None = None
    exercise_id: int
    exercise_title: str
    topic_id: int
    topic_title: str
    unit_id: int
    unit_title: str
    correct: bool
    answer: Any
    correct_answer: Any
    xp_earned: int
    points_earned: int
    attempted_at: datetime


class AttemptHistoryResponse(BaseModel):
    items: list[AttemptHistoryItem]
    total: int
    page: int
    pages: int
    limit: int


class MyClassItem(BaseModel):
    id: int
    name: str
    subject: str | None = None
    invite_code: str
    enrolled_at: datetime | None = None
    model_config = {"from_attributes": True}
