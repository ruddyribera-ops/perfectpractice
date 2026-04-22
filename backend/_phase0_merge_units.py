"""
PHASE 0.4 — Merge duplicate units (only true duplicates: same title + same topic)
Only one case: 'Fracciones equivalentes' under topic 108, units 127 vs 169
Keep 127 (more exercises), delete 169, reassign lessons/exercises.
"""
import sys, asyncio
sys.path.insert(0, '/app')
from sqlalchemy import text
from app.core.database import AsyncSessionLocal


# {duplicate_unit_id}: {canonical_unit_id}
UNITS_REMAP = {169: 127}
UNITS_TO_DELETE = [169]


async def main():
    async with AsyncSessionLocal() as db:
        print("=" * 60)
        print("PHASE 0.4 — MERGE DUPLICATE UNITS")
        print("=" * 60)

        print("\n[STATE] Units to process:")
        for dup_id in UNITS_TO_DELETE:
            r = await db.execute(text("""
                SELECT u.id, u.title, t.title as topic,
                       (SELECT COUNT(*) FROM lessons WHERE unit_id = u.id) as lessons,
                       (SELECT COUNT(*) FROM exercises WHERE unit_id = u.id) as exercises
                FROM units u
                JOIN topics t ON t.id = u.topic_id
                WHERE u.id = :id
            """), {"id": dup_id})
            row = r.fetchone()
            print(f"  Unit {dup_id}: '{row[1]}' (topic='{row[2]}') — {row[3]} lessons, {row[4]} exercises")

        print("\n[STEP 1] Remap lessons.unit_id from duplicate → canonical:")
        for dup_id, canon_id in UNITS_REMAP.items():
            r = await db.execute(text("""
                UPDATE lessons SET unit_id = :canon_id WHERE unit_id = :dup_id RETURNING id
            """), {"canon_id": canon_id, "dup_id": dup_id})
            rows = r.fetchall()
            print(f"  Unit {dup_id} → {canon_id}: {len(rows)} lessons remapped")

        print("\n[STEP 2] Remap exercises.unit_id from duplicate → canonical:")
        for dup_id, canon_id in UNITS_REMAP.items():
            r = await db.execute(text("""
                UPDATE exercises SET unit_id = :canon_id WHERE unit_id = :dup_id RETURNING id
            """), {"canon_id": canon_id, "dup_id": dup_id})
            rows = r.fetchall()
            print(f"  Unit {dup_id} → {canon_id}: {len(rows)} exercises remapped")

        print("\n[STEP 3] Delete duplicate units:")
        for dup_id in UNITS_TO_DELETE:
            r = await db.execute(text("DELETE FROM units WHERE id = :id RETURNING id, title"), {"id": dup_id})
            deleted = r.fetchone()
            if deleted:
                print(f"  ✅ Deleted unit {dup_id}: '{deleted[1]}'")

        await db.commit()
        print("\n✅ All committed!")

        # ── VERIFICATION ────────────────────────────────────────
        print("\n" + "=" * 60)
        print("VERIFICATION")
        print("=" * 60)

        r = await db.execute(text("""
            SELECT u.title, t.title, COUNT(*) as cnt
            FROM units u
            JOIN topics t ON t.id = u.topic_id
            GROUP BY u.title, t.title, t.id
            HAVING COUNT(*) > 1
        """))
        dup = r.fetchall()
        print(f"\n[1] Duplicate units (same title+topic): {len(dup)} {'✅ NONE' if not dup else '❌ FAIL'}")
        for row in dup: print(f"   ❌ '{row[0]}' x{row[1]}")

        r = await db.execute(text("SELECT COUNT(*) FROM lessons WHERE unit_id NOT IN (SELECT id FROM units)"))
        orphan_l = r.scalar()
        print(f"[2] Orphan lessons: {orphan_l} {'✅' if not orphan_l else '❌'}")

        r = await db.execute(text("SELECT COUNT(*) FROM exercises WHERE unit_id NOT IN (SELECT id FROM units)"))
        orphan_e = r.scalar()
        print(f"[3] Orphan exercises: {orphan_e} {'✅' if not orphan_e else '❌'}")

        totals = await db.execute(text("""
            SELECT
                (SELECT COUNT(*) FROM topics),
                (SELECT COUNT(*) FROM units),
                (SELECT COUNT(*) FROM lessons),
                (SELECT COUNT(*) FROM exercises)
        """))
        row = totals.fetchone()
        print(f"\n[4] Totals — Topics: {row[0]}, Units: {row[1]}, Lessons: {row[2]}, Exercises: {row[3]}")

        all_ok = not dup and not orphan_l and not orphan_e
        print(f"\n{'✅ PROCEED TO PHASE 0.5' if all_ok else '❌ ISSUES REMAIN'}")

asyncio.run(main())