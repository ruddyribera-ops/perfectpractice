from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Any

class TopicTreeResponse(BaseModel):
    id: int
    slug: str
    title: str
    description: Optional[str]
    icon_name: Optional[str]
    children: list["TopicTreeResponse"] = []
    class Config:
        from_attributes = True

class UnitResponse(BaseModel):
    id: int
    slug: str
    title: str
    description: Optional[str]
    order_index: int
    class Config:
        from_attributes = True

class TopicDetailResponse(BaseModel):
    id: int
    slug: str
    title: str
    description: Optional[str]
    icon_name: Optional[str]
    units: list[UnitResponse] = []
    class Config:
        from_attributes = True

class LessonResponse(BaseModel):
    id: int
    unit_id: int
    title: str
    content: str
    content_type: str = "text"
    order_index: int
    class Config:
        from_attributes = True

class LessonDetailResponse(BaseModel):
    id: int
    unit_id: int
    unit_slug: str
    title: str
    content: str
    content_type: str = "text"
    order_index: int
    exercises: list["ExerciseResponse"] = []
    class Config:
        from_attributes = True

class ExerciseResponse(BaseModel):
    id: int
    unit_id: int
    lesson_id: Optional[int]
    slug: str
    title: str
    exercise_type: str
    difficulty: str
    points_value: int
    data: dict
    hints: Optional[list[str]]
    is_anked: bool
    is_summative: bool
    class Config:
        from_attributes = True

class UnitDetailResponse(BaseModel):
    id: int
    topic_id: int
    slug: str
    title: str
    description: Optional[str]
    order_index: int
    exercises: list[ExerciseResponse] = []
    lessons: list[LessonResponse] = []
    class Config:
        from_attributes = True


class ExercisePickerItem(BaseModel):
    """Minimal exercise info for the assignment picker."""
    id: int
    title: str
    exercise_type: str
    difficulty: str
    points_value: int
    lesson_title: Optional[str] = None
    unit_title: str


class UnitWithExercises(BaseModel):
    """Unit with its exercises flattened for the picker."""
    id: int
    title: str
    slug: str
    exercises: list[ExercisePickerItem]


class TopicWithExercises(BaseModel):
    """Full topic tree with exercises for assignment creation."""
    id: int
    slug: str
    title: str
    units: list[UnitWithExercises]
