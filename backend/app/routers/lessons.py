from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.core.database import get_db
from app.core.security import get_current_user_required
from app.models.user import User
from app.models.curriculum import Lesson, Exercise, Unit
from app.schemas.curriculum import LessonResponse, LessonDetailResponse, ExerciseResponse

router = APIRouter()


@router.get("/unit/{unit_id}", response_model=List[LessonResponse])
async def get_lessons_for_unit(unit_id: int, user: User = Depends(get_current_user_required), db: AsyncSession = Depends(get_db)):
    """Get all lessons for a unit, ordered by order_index."""
    result = await db.execute(
        select(Lesson).where(Lesson.unit_id == unit_id).order_by(Lesson.order_index)
    )
    lessons = result.scalars().all()
    return [
        LessonResponse(
            id=l.id,
            unit_id=l.unit_id,
            title=l.title,
            content=l.content,
            content_type=l.content_type,
            order_index=l.order_index,
        )
        for l in lessons
    ]


@router.get("/{lesson_id}", response_model=LessonDetailResponse)
async def get_lesson(lesson_id: int, user: User = Depends(get_current_user_required), db: AsyncSession = Depends(get_db)):
    """Get a lesson with its exercises."""
    result = await db.execute(select(Lesson).where(Lesson.id == lesson_id))
    lesson = result.scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    # Get unit for slug
    unit_result = await db.execute(select(Unit).where(Unit.id == lesson.unit_id))
    unit = unit_result.scalar_one_or_none()

    # Get exercises for this lesson
    exercises_result = await db.execute(
        select(Exercise).where(Exercise.lesson_id == lesson_id)
    )
    exercises = exercises_result.scalars().all()

    exercise_responses = []
    for e in exercises:
        data = e.data.copy()
        data.pop("correct_answer", None)
        choices = data.pop("choices", None)
        options = data.pop("options", None)
        exercise_responses.append(ExerciseResponse(
            id=e.id,
            unit_id=e.unit_id,
            lesson_id=e.lesson_id,
            slug=e.slug,
            title=e.title,
            exercise_type=e.exercise_type.value if hasattr(e.exercise_type, 'value') else str(e.exercise_type),
            difficulty=e.difficulty.value if hasattr(e.difficulty, 'value') else str(e.difficulty),
            points_value=e.points_value,
            data={"question": data.get("question", ""), "options": choices or options, "explanation": data.get("explanation", "")},
            hints=e.hints,
            is_anked=e.is_anked,
            is_summative=e.is_summative
        ))

    return LessonDetailResponse(
        id=lesson.id,
        unit_id=lesson.unit_id,
        unit_slug=unit.slug if unit else "",
        title=lesson.title,
        content=lesson.content,
        content_type=lesson.content_type,
        order_index=lesson.order_index,
        exercises=exercise_responses
    )
