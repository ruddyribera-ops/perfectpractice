"""
PHASE 0.5 — Re-index order_index for units and lessons only.
(Topics have no order_index column — ordered by id.)
"""
import sys, asyncio
sys.path.insert(0, '/app')
from sqlalchemy import text
from app.core.database import AsyncSessionLocal


async def main():
    async with AsyncSessionLocal() as db:
        print("=" * 60)
        print("PHASE 0.5 — RE-INDEX ORDER_INDEX")
        print("=" * 60)

        # Units: order by order_index within each topic
        print("\n[STEP 1] Re-index units (per topic):")
        r = await db.execute(text("SELECT DISTINCT topic_id FROM units ORDER BY topic_id"))
        topic_ids = [row[0] for row in r.fetchall()]
        total_units = 0
        for tid in topic_ids:
            r = await db.execute(text("""
                SELECT id FROM units WHERE topic_id = :tid ORDER BY order_index, id
            """), {"tid": tid})
            unit_ids = [row[0] for row in r.fetchall()]
            for new_idx, uid in enumerate(unit_ids):
                await db.execute(text("UPDATE units SET order_index = :new_idx WHERE id = :uid"), {"new_idx": new_idx, "uid": uid})
            total_units += len(unit_ids)
        print(f"  Re-indexed {total_units} units across {len(topic_ids)} topics")

        # Lessons: order by order_index within each unit
        print("\n[STEP 2] Re-index lessons (per unit):")
        r = await db.execute(text("SELECT DISTINCT unit_id FROM lessons ORDER BY unit_id"))
        unit_ids = [row[0] for row in r.fetchall()]
        total_lessons = 0
        for uid in unit_ids:
            r = await db.execute(text("""
                SELECT id FROM lessons WHERE unit_id = :uid ORDER BY order_index, id
            """), {"uid": uid})
            lesson_ids = [row[0] for row in r.fetchall()]
            for new_idx, lid in enumerate(lesson_ids):
                await db.execute(text("UPDATE lessons SET order_index = :new_idx WHERE id = :lid"), {"new_idx": new_idx, "lid": lid})
            total_lessons += len(lesson_ids)
        print(f"  Re-indexed {total_lessons} lessons across {len(unit_ids)} units")

        await db.commit()

        # ── VERIFICATION ────────────────────────────────────────
        print("\n" + "=" * 60)
        print("VERIFICATION")
        print("=" * 60)

        # Check for gaps or duplicates in unit order_index per topic
        r = await db.execute(text("""
            SELECT topic_id, order_index, COUNT(*) as cnt
            FROM units
            GROUP BY topic_id, order_index
            HAVING COUNT(*) > 1
        """))
        dup = r.fetchall()
        print(f"\n[1] Unit order_index duplicates (per topic): {len(dup)} {'✅ NONE' if not dup else '❌ FAIL'}")
        for row in dup: print(f"   Topic {row[0]}, order_index={row[1]}: x{row[2]}")

        # Check for gaps or duplicates in lesson order_index per unit
        r = await db.execute(text("""
            SELECT unit_id, order_index, COUNT(*) as cnt
            FROM lessons
            GROUP BY unit_id, order_index
            HAVING COUNT(*) > 1
        """))
        dup = r.fetchall()
        print(f"[2] Lesson order_index duplicates (per unit): {len(dup)} {'✅ NONE' if not dup else '❌ FAIL'}")

        # Show final totals
        totals = await db.execute(text("""
            SELECT
                (SELECT COUNT(*) FROM topics),
                (SELECT COUNT(*) FROM units),
                (SELECT COUNT(*) FROM lessons),
                (SELECT COUNT(*) FROM exercises)
        """))
        row = totals.fetchone()
        print(f"\n[3] Final totals — Topics: {row[0]}, Units: {row[1]}, Lessons: {row[2]}, Exercises: {row[3]}")

        print("\n✅ PHASE 0.5 COMPLETE — PROCEED TO PHASE 0.6")

asyncio.run(main())