"""
PHASE 0.3 FINAL — Complete the merge cleanly
──────────────────────────────────────────
Due to FK constraint ordering (units → topics, then student_topic_progress → topics),
we must execute in this exact order:
  1. UPDATE units SET topic_id WHERE duplicate_topic_id
  2. DELETE units that were duplicate (already done in v1)
  3. UPDATE student_topic_progress SET topic_id WHERE duplicate_topic_id
  4. DELETE duplicate topics
"""
import sys, asyncio
sys.path.insert(0, '/app')
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def main():
    async with AsyncSessionLocal() as db:
        print("PHASE 0.3 FINAL — fixing remaining FKs")

        # STEP A: Fix units pointing to topic 82 (must happen before topic delete)
        r = await db.execute(text("SELECT id, title FROM units WHERE topic_id = 82"))
        units_82 = r.fetchall()
        print(f"Units still on topic 82: {units_82}")
        if units_82:
            await db.execute(text("UPDATE units SET topic_id = 108 WHERE topic_id = 82"))
            print(f"  → remapped {len(units_82)} units to topic 108")

        # STEP B: Fix student_topic_progress for topic 82
        r = await db.execute(text("SELECT COUNT(*) FROM student_topic_progress WHERE topic_id = 82"))
        stp_82 = r.scalar()
        if stp_82:
            await db.execute(text("UPDATE student_topic_progress SET topic_id = 108 WHERE topic_id = 82"))
            print(f"  → remapped {stp_82} stp rows for topic 82")

        # STEP C: Delete topic 82
        r = await db.execute(text("DELETE FROM topics WHERE id = 82 RETURNING id"))
        print(f"  → deleted topic 82: {r.rowcount} rows affected")

        await db.commit()
        print("\n✅ Topic 82 resolved!")

        # Verify what's left
        r = await db.execute(text("SELECT id FROM topics WHERE id IN (70, 82)"))
        print(f"Topics 70+82 still existing: {r.fetchall()}")

        # Full verification
        r = await db.execute(text("SELECT title, COUNT(*) FROM topics GROUP BY title HAVING COUNT(*) > 1"))
        dup = r.fetchall()
        print(f"\n[VERIFICATION] Duplicate topic titles: {len(dup)} {'✅ NONE' if not dup else '❌'}")
        for row in dup: print(f"  '{row[0]}' x{row[1]}")

        r = await db.execute(text("SELECT title, COUNT(*) FROM units GROUP BY title HAVING COUNT(*) > 1"))
        dup_u = r.fetchall()
        print(f"[VERIFICATION] Duplicate unit titles: {len(dup_u)} {'✅ NONE' if not dup_u else '❌'}")

        totals = await db.execute(text("SELECT (SELECT COUNT(*) FROM topics), (SELECT COUNT(*) FROM units), (SELECT COUNT(*) FROM lessons), (SELECT COUNT(*) FROM exercises)"))
        row = totals.fetchone()
        print(f"\nTotals — Topics: {row[0]}, Units: {row[1]}, Lessons: {row[2]}, Exercises: {row[3]}")

asyncio.run(main())
