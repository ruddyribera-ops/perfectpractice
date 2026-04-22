"""
PHASE 0.3 v3 — Fix remaining FK chains after partial merge
─────────────────────────────────────────────────────────
The previous two runs partially completed Steps 1-4.
This script fixes the remaining broken FK chains:
  - units.topic_id still points to duplicate topic IDs
  - then deletes the duplicate topics

Run AFTER the partial merge (which already committed).
"""
import sys, asyncio
sys.path.insert(0, '/app')
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

# Units that still reference duplicate topic IDs
# (from the Scout findings — these were NOT remapped in Step 2 of the first run)
UNIT_TOPIC_REMAP = {
    # {unit_id}: {canonical_topic_id}   ← units that still have wrong topic_id
    121: 98,   # 'Sumar fracciones' topic 78 → 98
    122: 98,   # 'Comparar fracciones' topic 78 → 98
    131: 95,   # 'Rango y mediana' topic 85 → 95
    175: 110,  # 'Probabilidad y estadística' topic 113 → 110
    103: 103, # 'Contar hasta 20' topic 67 → 103 (keep same — id=103 is already canonical!)
    104: 103, # 'Ordenar números' topic 67 → 103
}

# student_topic_progress FK: topic_id → topics(id)
STP_REMAP = {
    78:  98,
    85:  95,
    113: 110,
    67:  103,
    118: 90,
    70:  102,
    82:  108,
    111: 108,
}

# Topics still to delete (after all FKs are fixed)
TOPICS_TO_DELETE = [78, 85, 113, 67, 118, 70, 82, 111]


async def main():
    async with AsyncSessionLocal() as db:
        print("=" * 60)
        print("PHASE 0.3 v3 — FIX REMAINING FK CHAINS")
        print("=" * 60)

        print("\n[CHECK] Current state of duplicate topic IDs:")
        for tid in TOPICS_TO_DELETE:
            r = await db.execute(text("""
                SELECT
                    (SELECT COUNT(*) FROM units WHERE topic_id = :tid) as units_count,
                    (SELECT COUNT(*) FROM student_topic_progress WHERE topic_id = :tid) as stp_count
            """), {"tid": tid})
            row = r.fetchone()
            print(f"  Topic {tid}: {row[0]} units, {row[1]} stp rows still referencing it")

        print("\nSTEP 2.6 — Fix units.topic_id for units still pointing to duplicate topics")
        for unit_id, canon_topic_id in UNIT_TOPIC_REMAP.items():
            r = await db.execute(text("""
                UPDATE units SET topic_id = :canon_id WHERE id = :unit_id RETURNING id, title, topic_id
            """), {"canon_id": canon_topic_id, "unit_id": unit_id})
            rows = r.fetchall()
            if rows:
                print(f"  Unit {unit_id} → topic {canon_topic_id}: OK ('{rows[0][1]}')")
            else:
                print(f"  Unit {unit_id}: NOT FOUND (may have already been remapped)")

        print("\nSTEP 2.7 — Fix student_topic_progress.topic_id")
        for dup_id, canon_id in STP_REMAP.items():
            r = await db.execute(text("""
                UPDATE student_topic_progress SET topic_id = :canon_id WHERE topic_id = :dup_id
                RETURNING id
            """), {"canon_id": canon_id, "dup_id": dup_id})
            rows = r.fetchall()
            print(f"  Topic {dup_id} → {canon_id}: {len(rows)} stp rows remapped")

        print("\nSTEP 5 — Delete duplicate topics (final)")
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
