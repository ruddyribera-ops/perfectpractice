"""
PHASE 0.3 v4 — Complete remaining unit topic FK fixes
────────────────────────────────────────────────────
More units were found referencing duplicate topic IDs:
  Unit 180 'Volumen del prisma'     → topic 118 (needs → 90)
  Unit 110 'Tamaño y longitud'     → topic 70  (needs → 102)
  Unit 127 'Fracciones equivalentes'→ topic 82  (needs → 108)
  Unit 128 'Introducción a decimales'→ topic 82 (needs → 108)
"""
import sys, asyncio
sys.path.insert(0, '/app')
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

EXTRA_UNIT_REMAP = {
    180: 90,   # Volumen del prisma → canonical Volumen topic
    110: 102,  # Tamaño y longitud → canonical Medición topic
    127: 108,  # Fracciones equivalentes → canonical Fracciones y decimales topic
    128: 108,  # Introducción a decimales → canonical Fracciones y decimales topic
}

TOPICS_TO_DELETE = [118, 70, 82, 111]


async def main():
    async with AsyncSessionLocal() as db:
        print("=" * 60)
        print("PHASE 0.3 v4 — COMPLETE REMAINING FIXES")
        print("=" * 60)

        print("\nSTEP 2.8 — Fix remaining unit topic FKs")
        for unit_id, canon_topic_id in EXTRA_UNIT_REMAP.items():
            r = await db.execute(text("""
                UPDATE units SET topic_id = :canon_id WHERE id = :unit_id RETURNING id, title, topic_id
            """), {"canon_id": canon_topic_id, "unit_id": unit_id})
            rows = r.fetchall()
            if rows:
                print(f"  Unit {unit_id} → topic {canon_topic_id}: OK ('{rows[0][1]}')")
            else:
                print(f"  Unit {unit_id}: NOT FOUND (may already be remapped)")

        print("\nSTEP 5b — Delete remaining duplicate topics")
        for dup_id in TOPICS_TO_DELETE:
            r = await db.execute(text("""
                DELETE FROM topics WHERE id = :id RETURNING id, title
            """), {"id": dup_id})
            deleted = r.rowcount
            print(f"  Deleted topic {dup_id}: {'OK' if deleted else 'NOT FOUND'}")

        await db.commit()
        print("\n✅ Committed!")

        # ── VERIFICATION ─────────────────────────────────────────
        print("\n" + "=" * 60)
        print("PHASE 0.6 — POST-MERGE VERIFICATION")
        print("=" * 60)

        r = await db.execute(text("SELECT title, COUNT(*) FROM units GROUP BY title HAVING COUNT(*) > 1"))
        dup_units = r.fetchall()
        print(f"\n[1] Duplicate unit titles: {len(dup_units)} {'✅ NONE' if len(dup_units) == 0 else '❌ FAIL'}")

        r = await db.execute(text("SELECT title, COUNT(*) FROM topics GROUP BY title HAVING COUNT(*) > 1"))
        dup_topics = r.fetchall()
        print(f"[2] Duplicate topic titles: {len(dup_topics)} {'✅ NONE' if len(dup_topics) == 0 else '❌ FAIL'}")
        for row in dup_topics:
            print(f"     ❌ '{row[0]}' appears {row[1]} times")

        r = await db.execute(text("SELECT COUNT(*) FROM lessons WHERE unit_id NOT IN (SELECT id FROM units)"))
        orphans = r.scalar()
        print(f"[3] Orphan lessons: {orphans} {'✅ NONE' if orphans == 0 else '❌ FAIL'}")

        r = await db.execute(text("SELECT COUNT(*) FROM units WHERE topic_id NOT IN (SELECT id FROM topics)"))
        orphan_u = r.scalar()
        print(f"[4] Orphan units: {orphan_u} {'✅ NONE' if orphan_u == 0 else '❌ FAIL'}")

        r = await db.execute(text("SELECT COUNT(*) FROM student_topic_progress WHERE topic_id NOT IN (SELECT id FROM topics)"))
        orphan_stp = r.scalar()
        print(f"[5] Orphan student_topic_progress: {orphan_stp} {'✅ NONE' if orphan_stp == 0 else '❌ FAIL'}")

        totals = await db.execute(text("""
            SELECT
                (SELECT COUNT(*) FROM topics) as topics,
                (SELECT COUNT(*) FROM units) as units,
                (SELECT COUNT(*) FROM lessons) as lessons,
                (SELECT COUNT(*) FROM exercises) as exercises
        """))
        row = totals.fetchone()
        print(f"\n[6] Totals — Topics: {row[0]}, Units: {row[1]}, Lessons: {row[2]}, Exercises: {row[3]}")

        all_ok = len(dup_units) == 0 and len(dup_topics) == 0 and orphans == 0 and orphan_u == 0 and orphan_stp == 0
        print(f"\n{'✅ ALL CHECKS PASSED — PHASE 0.3 COMPLETE' if all_ok else '❌ SOME CHECKS FAILED'}")

asyncio.run(main())
