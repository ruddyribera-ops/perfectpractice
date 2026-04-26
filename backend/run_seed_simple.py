#!/usr/bin/env python3
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from seed.curriculum_seed import TOPICS

async def main():
    print("=" * 60)
    print("CURRICULUM SEED - COUNT PREVIEW")
    print("=" * 60)

    total_topics = len(TOPICS)
    total_units = sum(len(topic["units"]) for topic in TOPICS)
    total_lessons = sum(sum(len(u["lessons"]) for u in topic["units"]) for topic in TOPICS)
    total_exercises = sum(sum(len(u["exercises"]) for u in topic["units"]) for topic in TOPICS)

    print(f"\nWill create:")
    print(f"   Topics: {total_topics}")
    print(f"   Units: {total_units}")
    print(f"   Lessons: {total_lessons}")
    print(f"   Exercises: {total_exercises}")

    print(f"\nTopics breakdown:")
    for topic in TOPICS:
        units_count = len(topic["units"])
        exercises_count = sum(len(u["exercises"]) for u in topic["units"])
        print(f"  - {topic['title']}: {units_count} units, {exercises_count} exercises")

    print("\nTo execute the seed in Railway, run:")
    print("  cd backend")
    print("  railway run python seed/curriculum_seed.py --commit")

if __name__ == "__main__":
    asyncio.run(main())
