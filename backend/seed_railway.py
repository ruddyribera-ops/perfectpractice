"""
Railway Seed Runner — runs the full curriculum_seed.py inside the Railway container.

This script runs ON Railway (via railway run), not locally.
It reads DATABASE_URL from the Railway environment and calls seed_topics().

Usage: railway run -s lucid-serenity python seed_railway.py
"""
import asyncio
import sys
from pathlib import Path

# Allow imports from the backend package
sys.path.insert(0, str(Path(__file__).parent))

from seed.curriculum_seed import seed_topics, verify_seed, AsyncSessionLocal


async def run():
    print("=" * 60)
    print("FULL CURRICULUM SEED — Railway Runner")
    print("=" * 60)

    # Show current state
    print("\n📊 Current database state:")
    t, u, l, e = await verify_seed()
    print(f"   Topics: {t}, Units: {u}, Lessons: {l}, Exercises: {e}")

    if t > 0:
        print("\n⚠️  DB already has content.")
        print("   Skipping full re-seed to avoid duplicates.")
        print("   If you want to replace all content, clear the DB first.")
        return

    print("\n🚀 Running full seed...")
    async with AsyncSessionLocal() as db:
        t, u, l, e = await seed_topics(db)
        await db.commit()
        print(f"\n✅ Seed complete! Created: {t} topics, {u} units, {l} lessons, {e} exercises")

    print("\n📊 Final database state:")
    t, u, l, e = await verify_seed()
    print(f"   Topics: {t}, Units: {u}, Lessons: {l}, Exercises: {e}")


if __name__ == "__main__":
    asyncio.run(run())