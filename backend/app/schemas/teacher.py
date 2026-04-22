from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ClassCreateRequest(BaseModel):
    name: str
    subject: str

class ClassResponse(BaseModel):
    id: int
    name: str
    teacher_id: int
    subject: str
    invite_code: str
    created_at: datetime
    student_count: int = 0
    avg_mastery: float = 0.0
    class Config:
        from_attributes = True


class ClassDetailResponse(BaseModel):
    id: int
    name: str
    teacher_id: int
    subject: str
    invite_code: str
    created_at: datetime
    student_count: int
    assignment_count: int
    class Config:
        from_attributes = True

class ClassStudentsResponse(BaseModel):
    student_id: int
    name: str
    email: str
    grade: int
    points: int
    level: int
    current_streak: int
    avg_mastery: float
    enrolled_at: datetime
    last_active: Optional[datetime] = None
    exercises_completed: int = 0
    model_config = {"from_attributes": True}

class AssignmentCreateRequest(BaseModel):
    class_id: Optional[int] = None  # Optional when using URL-scoped endpoint
    title: str
    description: Optional[str] = None
    exercise_ids: list[int]
    due_date: Optional[datetime] = None

class AssignmentResponse(BaseModel):
    id: int
    class_id: int
    title: str
    description: Optional[str]
    due_date: Optional[datetime]
    created_at: datetime
    class Config:
        from_attributes = True
