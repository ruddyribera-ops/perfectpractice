"""
PHASE 0.4 — Find all duplicate units with full context
"""
import sys, asyncio
sys.path.insert(0, '/app')
from sqlalchemy import text
from app.core.database import AsyncSessionLocal


async def main():
    async with AsyncSessionLocal() as db:
        print("=" * 60)
        print("PHASE 0.4 — DUPLICATE UNITS ANALYSIS")
        print("=" * 60)

        # Find duplicate unit titles
        r = await db.execute(text("""
            SELECT u.title, t.title as topic, t.id as topic_id, COUNT(*) as cnt
            FROM units u
            JOIN topics t ON t.id = u.topic_id
            GROUP BY u.title, t.title, t.id
            HAVING COUNT(*) > 1
            ORDER BY u.title
        """))
        dup_groups = r.fetchall()

        print(f"\n[1] Duplicate unit TITLE+TOPIC pairs: {len(dup_groups)}")
        for row in dup_groups:
            print(f"   '{row[0]}' (topic_id={row[2]}, topic='{row[1]}') x{row[3]}")

        # For each duplicate group, list the unit IDs and their lesson/exercise counts
        print("\n[2] Full breakdown of each duplicate unit:")
        for row in dup_groups:
            title, topic_title, topic_id, cnt = row
            r2 = await db.execute(text("""
                SELECT u.id, u.title, u.topic_id,
                       (SELECT COUNT(*) FROM lessons WHERE unit_id = u.id) as lesson_count,
                       (SELECT COUNT(*) FROM exercises WHERE unit_id = u.id) as exercise_count
                FROM units u
                WHERE u.title = :title AND u.topic_id = :topic_id
                ORDER BY u.id
            """), {"title": title, "topic_id": topic_id})
            units = r2.fetchall()
            print(f"\n   Topic '{topic_title}', Unit '{title}':")
            for u in units:
                print(f"     Unit id={u[0]}: {u[3]} lessons, {u[4]} exercises")

        all_ok = len(dup_groups) == 0
        print(f"\n{'✅ NO duplicate units' if all_ok else f'❌ {len(dup_groups)} duplicate groups — see above for IDs'}")

asyncio.run(main())