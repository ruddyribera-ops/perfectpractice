"""
PHASE 0.3 COMPLETE CLEANUP — Delete ALL remaining duplicate topics
────────────────────────────────────────────────────────────────
Order matters (FK chain):
  1. Fix all units.topic_id → canonical
  2. Fix all student_topic_progress.topic_id → canonical
  3. DELETE duplicate topics
"""
import sys, asyncio
sys.path.insert(0, '/app')
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

# {duplicate_topic_id}: {canonical_topic_id}
STP_REMAP = {78: 98, 85: 95, 113: 110, 67: 103, 118: 90, 70: 102, 111: 108}
UNITS_REMAP = {78: 98, 85: 95, 113: 110, 67: 103, 118: 90, 70: 102, 111: 108}
TOPICS_TO_DELETE = [78, 85, 113, 67, 118, 70, 111]


async def main():
    async with AsyncSessionLocal() as db:
        print("=" * 60)
        print("PHASE 0.3 COMPLETE CLEANUP")
        print("=" * 60)

        # Step 1: Check and print current state
        print("\n[STATE] Remaining duplicate topic IDs:")
        for tid in TOPICS_TO_DELETE:
            r = await db.execute(text("""
                SELECT
                    (SELECT COUNT(*) FROM units WHERE topic_id = :tid),
                    (SELECT COUNT(*) FROM student_topic_progress WHERE topic_id = :tid)
            """), {"tid": tid})
            row = r.fetchone()
            print(f"  Topic {tid}: {row[0]} units, {row[1]} stp rows")

        # Step 2: Fix student_topic_progress FK FIRST (must be before unit FK)
        print("\n[STEP 1] Remap student_topic_progress.topic_id:")
        for dup_id, canon_id in STP_REMAP.items():
            r = await db.execute(text("""
                UPDATE student_topic_progress
                SET topic_id = :canon_id
                WHERE topic_id = :dup_id
                RETURNING id
            """), {"canon_id": canon_id, "dup_id": dup_id})
            rows = r.fetchall()
            print(f"  Topic {dup_id} → {canon_id}: {len(rows)} rows")

        # Step 2b: Fix units.topic_id FK BEFORE deleting topics
        print("\n[STEP 2] Remap units.topic_id:")
        for dup_id, canon_id in UNITS_REMAP.items():
            r = await db.execute(text("""
                UPDATE units
                SET topic_id = :canon_id
                WHERE topic_id = :dup_id
                RETURNING id
            """), {"canon_id": canon_id, "dup_id": dup_id})
            rows = r.fetchall()
            print(f"  Topic {dup_id} → {canon_id}: {len(rows)} units remapped")

        # Step 3: Now delete duplicate topics (no more FK conflicts)
        print("\n[STEP 2] Delete duplicate topics:")
        for dup_id in TOPICS_TO_DELETE:
            r = await db.execute(text("DELETE FROM topics WHERE id = :id RETURNING id, title"), {"id": dup_id})
            deleted = r.fetchall()
            if deleted:
                print(f"  ✅ Deleted topic {dup_id}: '{deleted[0][1]}'")
            else:
                print(f"  ⚠️  Topic {dup_id}: already deleted or not found")

        await db.commit()
        print("\n✅ All committed!")

        # ── FULL VERIFICATION ───────────────────────────────────
        print("\n" + "=" * 60)
        print("PHASE 0.6 — FULL POST-MERGE VERIFICATION")
        print("=" * 60)

        r = await db.execute(text("SELECT title, COUNT(*) FROM units GROUP BY title HAVING COUNT(*) > 1"))
        dup_u = r.fetchall()
        print(f"\n[1] Duplicate unit titles: {len(dup_u)} {'✅ NONE' if not dup_u else '❌ FAIL'}")
        for row in dup_u: print(f"     ❌ '{row[0]}' x{row[1]}")

        r = await db.execute(text("SELECT title, COUNT(*) FROM topics GROUP BY title HAVING COUNT(*) > 1"))
        dup_t = r.fetchall()
        print(f"[2] Duplicate topic titles: {len(dup_t)} {'✅ NONE' if not dup_t else '❌ FAIL'}")
        for row in dup_t: print(f"     ❌ '{row[0]}' x{row[1]}")

        r = await db.execute(text("SELECT COUNT(*) FROM lessons WHERE unit_id NOT IN (SELECT id FROM units)"))
        print(f"[3] Orphan lessons: {r.scalar()} {'✅' if not r.scalar() else '❌'}")

        r = await db.execute(text("SELECT COUNT(*) FROM units WHERE topic_id NOT IN (SELECT id FROM topics)"))
        print(f"[4] Orphan units: {r.scalar()} {'✅' if not r.scalar() else '❌'}")

        r = await db.execute(text("SELECT COUNT(*) FROM student_topic_progress WHERE topic_id NOT IN (SELECT id FROM topics)"))
        print(f"[5] Orphan stp rows: {r.scalar()} {'✅' if not r.scalar() else '❌'}")

        totals = await db.execute(text("""
            SELECT
                (SELECT COUNT(*) FROM topics),
                (SELECT COUNT(*) FROM units),
                (SELECT COUNT(*) FROM lessons),
                (SELECT COUNT(*) FROM exercises)
        """))
        row = totals.fetchone()
        print(f"\n[6] Totals — Topics: {row[0]}, Units: {row[1]}, Lessons: {row[2]}, Exercises: {row[3]}")

        all_ok = not dup_u and not dup_t
        print(f"\n{'✅ MERGE COMPLETE — PROCEED TO PHASE 0.4' if all_ok else '❌ DUPLICATES REMAIN — STOP'}")

asyncio.run(main())
