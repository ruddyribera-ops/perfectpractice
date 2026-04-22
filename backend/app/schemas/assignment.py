from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Any

class AssignmentCreateRequest(BaseModel):
    class_id: int
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


class ExerciseResultItem(BaseModel):
    exercise_id: int
    exercise_title: str
    correct: bool
    points_earned: int
    xp_earned: int


class StudentAssignmentResult(BaseModel):
    student_id: int
    student_name: str
    score: Optional[float]
    completion_rate: float
    completed_at: Optional[datetime]
    started_at: Optional[datetime]
    exercises: list[ExerciseResultItem]


class AssignmentResultResponse(BaseModel):
    assignment_id: int
    title: str
    total_students: int
    completed_count: int
    avg_score: Optional[float]
    completion_rate: float
    results: list[StudentAssignmentResult]


class ExerciseInAssignment(BaseModel):
    id: int
    title: str
    exercise_type: str
    difficulty: str
    order_index: int
    status: str  # "not_started" | "in_progress" | "correct" | "incorrect"


class StudentAssignmentDetail(BaseModel):
    id: int
    title: str
    description: Optional[str]
    due_date: Optional[datetime]
    class_id: int
    class_name: str
    score: Optional[float]
    completion_rate: float
    exercises: list[ExerciseInAssignment]
    model_config = {"from_attributes": True}


class StudentAssignmentListItem(BaseModel):
    id: int
    title: str
    description: Optional[str]
    due_date: Optional[datetime]
    class_id: int
    class_name: str
    score: Optional[float]
    completion_rate: float
    completed_at: Optional[datetime]
    model_config = {"from_attributes": True}


class MyAssignmentsResponse(BaseModel):
    items: list[StudentAssignmentListItem]
    total: int
