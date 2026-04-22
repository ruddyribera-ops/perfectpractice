from pydantic import BaseModel
from typing import Optional

class LeaderboardEntry(BaseModel):
    rank: int
    student_id: int
    student_name: str
    points: int
    avatar_url: Optional[str]
    level: int


class LeaderboardMeResponse(BaseModel):
    student_id: int
    name: str
    weekly_rank: Optional[int]
    weekly_points: int
    monthly_rank: Optional[int]
    monthly_points: int
    all_time_rank: Optional[int]
    all_time_points: int
