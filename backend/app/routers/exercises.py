from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user_required
from app.models.user import User
from app.models.curriculum import Exercise
from app.schemas.curriculum import ExerciseResponse

router = APIRouter()

@router.get("/{exercise_id}", response_model=ExerciseResponse)
async def get_exercise(exercise_id: int, user: User = Depends(get_current_user_required), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Exercise).where(Exercise.id == exercise_id))
    exercise = result.scalar_one_or_none()
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")

    if user.role == "student":
        data = exercise.data.copy()
        correct_answer = data.pop("correct_answer", None)
        # Normalize choices to options for frontend compatibility
        choices = data.pop("choices", None)
        options = data.pop("options", None)
        return ExerciseResponse(
            id=exercise.id,
            unit_id=exercise.unit_id,
            lesson_id=exercise.lesson_id,
            slug=exercise.slug,
            title=exercise.title,
            exercise_type=exercise.exercise_type.value if hasattr(exercise.exercise_type, 'value') else str(exercise.exercise_type),
            difficulty=exercise.difficulty.value if hasattr(exercise.difficulty, 'value') else str(exercise.difficulty),
            points_value=exercise.points_value,
            data={"question": data.get("question", ""), "options": choices or options, "explanation": data.get("explanation", "")},
            hints=exercise.hints,
            is_anked=exercise.is_anked,
            is_summative=exercise.is_summative
        )

    return ExerciseResponse(
        id=exercise.id,
        unit_id=exercise.unit_id,
        lesson_id=exercise.lesson_id,
        slug=exercise.slug,
        title=exercise.title,
        exercise_type=exercise.exercise_type.value if hasattr(exercise.exercise_type, 'value') else str(exercise.exercise_type),
        difficulty=exercise.difficulty.value if hasattr(exercise.difficulty, 'value') else str(exercise.difficulty),
        points_value=exercise.points_value,
        data=exercise.data,
        hints=exercise.hints,
        is_anked=exercise.is_anked,
        is_summative=exercise.is_summative
    )