#!/usr/bin/env python3
"""Async seed script using asyncpg directly."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.curriculum import Topic, Unit, Lesson, Exercise
from seed.curriculum_seed import TOPICS

async def seed_all():
    """Seed curriculum using async session."""
    async with AsyncSessionLocal() as db:
        print("Starting async curriculum seed...")

        topic_count = 0
        unit_count = 0
        lesson_count = 0
        exercise_count = 0

        for topic_data in TOPICS:
            # Create topic
            topic = Topic(
                slug=topic_data["slug"],
                title=topic_data["title"],
                description=topic_data.get("description"),
                icon_name=topic_data.get("icon_name"),
            )
            db.add(topic)
            await db.flush()
            topic_count += 1
            print(f"Created topic: {topic.title}")

            # Create units
            for unit_data in topic_data.get("units", []):
                unit = Unit(
                    topic_id=topic.id,
                    slug=unit_data["slug"],
                    title=unit_data["title"],
                    description=unit_data.get("description"),
                    order_index=unit_data.get("order_index", 0),
                )
                db.add(unit)
                await db.flush()
                unit_count += 1

                # Create lessons
                lesson_map = {}
                for lesson_data in unit_data.get("lessons", []):
                    lesson = Lesson(
                        unit_id=unit.id,
                        title=lesson_data["title"],
                        content=lesson_data["content"],
                        order_index=lesson_data.get("order_index", 0),
                    )
                    db.add(lesson)
                    await db.flush()
                    lesson_count += 1
                    lesson_map[lesson_data["title"]] = lesson.id

                # Create exercises
                for ex_data in unit_data.get("exercises", []):
                    # Find lesson for this exercise
                    lesson_id = None
                    for lesson_data in unit_data.get("lessons", []):
                        if ex_data["slug"] in lesson_data.get("exercise_slugs", []):
                            lesson_id = lesson_map.get(lesson_data["title"])
                            break

                    exercise = Exercise(
                        unit_id=unit.id,
                        lesson_id=lesson_id,
                        slug=ex_data["slug"],
                        title=ex_data["title"],
                        exercise_type=ex_data["exercise_type"],
                        difficulty=ex_data["difficulty"],
                        points_value=ex_data["points"],
                        data=ex_data["data"],
                        hints=ex_data.get("hints"),
                        is_anked=ex_data.get("is_anked", False),
                        is_summative=ex_data.get("is_summative", False),
                    )
                    db.add(exercise)
                    exercise_count += 1

                print(f"  Unit: {unit.title} ({len(unit_data.get('exercises', []))} exercises)")

        # Commit all
        await db.commit()

        print(f"\nSeed complete!")
        print(f"Created: {topic_count} topics, {unit_count} units, {lesson_count} lessons, {exercise_count} exercises")

if __name__ == "__main__":
    asyncio.run(seed_all())
