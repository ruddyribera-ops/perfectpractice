from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List

from app.core.database import get_db
from app.core.security import get_current_user_required
from app.models.curriculum import Topic, Unit, Exercise, Lesson
from app.models.user import User
from app.schemas.curriculum import (
    TopicTreeResponse, TopicDetailResponse,
    TopicWithExercises, UnitWithExercises, ExercisePickerItem,
)

router = APIRouter()


@router.get("", response_model=List[TopicTreeResponse])
async def list_topics(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Topic)
        .where(Topic.parent_id == None)
        .options(selectinload(Topic.children))
    )
    topics = result.scalars().all()
    return [TopicTreeResponse.model_validate(t) for t in topics]


@router.get("/{slug}", response_model=TopicDetailResponse)
async def get_topic(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Topic)
        .where(Topic.slug == slug)
        .options(selectinload(Topic.units))
    )
    topic = result.scalar_one_or_none()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    return TopicDetailResponse.model_validate(topic)


@router.get("/picker/full", response_model=List[TopicWithExercises])
async def get_topic_picker_tree(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user_required),
):
    """
    Returns the full topic tree with all units and their exercises.
    Used by teachers to pick exercises when creating an assignment.
    """
    # Fetch all root topics with their units and exercises
    result = await db.execute(
        select(Topic)
        .where(Topic.parent_id == None)
        .options(
            selectinload(Topic.units).selectinload(Unit.exercises),
            selectinload(Topic.units).selectinload(Unit.lessons),
        )
    )
    topics = result.scalars().all()

    tree: list[TopicWithExercises] = []
    for topic in topics:
        units_data: list[UnitWithExercises] = []
        for unit in sorted(topic.units, key=lambda u: u.order_index or 0):
            # Build lesson_id → lesson_title map
            lesson_map: dict[int, str] = {
                lesson.id: lesson.title for lesson in unit.lessons
            }

            exercises_data: list[ExercisePickerItem] = [
                ExercisePickerItem(
                    id=ex.id,
                    title=ex.title,
                    exercise_type=ex.exercise_type.value,
                    difficulty=ex.difficulty.value,
                    points_value=ex.points_value,
                    lesson_title=lesson_map.get(ex.lesson_id) if ex.lesson_id else None,
                    unit_title=unit.title,
                )
                for ex in unit.exercises
            ]

            units_data.append(UnitWithExercises(
                id=unit.id,
                title=unit.title,
                slug=unit.slug,
                exercises=exercises_data,
            ))

        tree.append(TopicWithExercises(
            id=topic.id,
            slug=topic.slug,
            title=topic.title,
            units=units_data,
        ))

    return tree
