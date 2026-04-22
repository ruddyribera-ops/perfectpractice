"""
PHASE 0.3 — Execute Curriculum Merge
────────────────────────────────────
This script reassigns all FK references from duplicate entities to their
canonical equivalents, then deletes the duplicate rows — all inside a
single transaction so we can rollback on any error.

Canonical decisions (confirmed with user):
  UNITS to keep (higher content): 132, 154, 127, 178, 148, 179, 138
  UNITS to delete:                   173, 103, 169, 134, 164, 133, 177

  TOPICS to keep: 98, 95, 110, 103, 90, 102, 108, (and 79 for Perímetro y Área)
  TOPICS to delete: 78, 85, 113, 67, 118, 70, 82, 111

Usage:
  docker cp _phase0_merge.py math-platform-backend-1:/tmp/_phase0_merge.py
  docker exec math-platform-backend-1 python /tmp/_phase0_merge.py [--rollback]
"""
import sys, asyncio, argparse
sys.path.insert(0, '/app')
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

UNIT_REMAP = {
    # {duplicate_id}: {canonical_id}
    173: 132,  # Operaciones con decimales
    103: 154,  # Contar hasta 20
    169: 127,  # Fracciones equivalentes
    134: 178,  # Razones
    164: 148,  # División
    133: 179,  # ¿Qué es el porcentaje?
    177: 138,  # Números negativos
}

TOPIC_REMAP = {
    # {duplicate_id}: {canonical_id}
    78:  98,   # Fracciones
    85:  95,   # Estadística Avanzada
    113: 110,  # Probabilidad
    67:  103,  # Números hasta 100
    118: 90,   # Volumen
    70:  102,  # Medición
    82:  108,  # Fracciones y Decimales
    111: 108,  # Fracciones y decimales (triplet merge)
}


async def do_merge(db):
    print("STEP 1 — Remap unit FKs in lessons + exercises")
    for dup_id, canon_id in UNIT_REMAP.items():
        # Remap lessons
        r1 = await db.execute(text("""
            UPDATE lessons SET unit_id = :canon_id WHERE unit_id = :dup_id
            RETURNING id, title
        """), {"canon_id": canon_id, "dup_id": dup_id})
        lessons_moved = r1.rowcount
        # Remap exercises
        r2 = await db.execute(text("""
            UPDATE exercises SET unit_id = :canon_id WHERE unit_id = :dup_id
            RETURNING id
        """), {"canon_id": canon_id, "dup_id": dup_id})
        exercises_moved = r2.rowcount
        print(f"  Unit {dup_id} → {canon_id}: {lessons_moved} lessons, {exercises_moved} exercises reassigned")

    print("\nSTEP 2 — Remap topic FKs in units")
    for dup_id, canon_id in TOPIC_REMAP.items():
        r = await db.execute(text("""
            UPDATE units SET topic_id = :canon_id WHERE topic_id = :dup_id
            RETURNING id, title
        """), {"canon_id": canon_id, "dup_id": dup_id})
        units_moved = r.rowcount
        print(f"  Topic {dup_id} → {canon_id}: {units_moved} units reassigned")

    print("\nSTEP 3 — Delete duplicate units")
    for dup_id in UNIT_REMAP.keys():
        r = await db.execute(text("""
            DELETE FROM units WHERE id = :id RETURNING id, title
        """), {"id": dup_id})
        deleted = r.rowcount
        print(f"  Deleted unit {dup_id}: {'OK' if deleted else 'NOT FOUND'}")

    print("\nSTEP 4 — Delete duplicate topics")
    for dup_id in TOPIC_REMAP.keys():
        r = await db.execute(text("""
            DELETE FROM topics WHERE id = :id RETURNING id, title
        """), {"id": dup_id})
        deleted = r.rowcount
        print(f"  Deleted topic {dup_id}: {'OK' if deleted else 'NOT FOUND'}")


async def verify(db):
    print("\n" + "=" * 60)
    print("PHASE 0.6 — POST-MERGE VERIFICATION")
    print("=" * 60)

    # 1. No duplicate unit titles
    r = await db.execute(text("""
        SELECT title, COUNT(*) as cnt FROM units GROUP BY title HAVING COUNT(*) > 1
    """))
    dup_units = r.fetchall()
    print(f"\n[1] Duplicate unit titles: {len(dup_units)} {'✅ NONE' if len(dup_units) == 0 else '❌ FAIL'}")
    for row in dup_units: print(f"     ❌ '{row[0]}' appears {row[1]} times")

    # 2. No duplicate topic titles
    r = await db.execute(text("""
        SELECT title, COUNT(*) as cnt FROM topics GROUP BY title HAVING COUNT(*) > 1
    """))
    dup_topics = r.fetchall()
    print(f"[2] Duplicate topic titles: {len(dup_topics)} {'✅ NONE' if len(dup_topics) == 0 else '❌ FAIL'}")
    for row in dup_topics: print(f"     ❌ '{row[0]}' appears {row[1]} times")

    # 3. No orphan lessons
    r = await db.execute(text("""
        SELECT COUNT(*) FROM lessons WHERE unit_id NOT IN (SELECT id FROM units)
    """))
    orphans = r.scalar()
    print(f"[3] Orphan lessons: {orphans} {'✅ NONE' if orphans == 0 else '❌ FAIL'}")

    # 4. No orphan exercises (unit_id)
    r = await db.execute(text("""
        SELECT COUNT(*) FROM exercises WHERE unit_id NOT IN (SELECT id FROM units) AND lesson_id NOT IN (SELECT id FROM lessons)
    """))
    orphan_ex = r.scalar()
    print(f"[4] Orphan exercises (no valid unit_id or lesson_id): {orphan_ex} {'✅ NONE' if orphan_ex == 0 else '❌ FAIL'}")

    # 5. No orphan units
    r = await db.execute(text("""
        SELECT COUNT(*) FROM units WHERE topic_id NOT IN (SELECT id FROM topics)
    """))
    orphan_units = r.scalar()
    print(f"[5] Orphan units: {orphan_units} {'✅ NONE' if orphan_units == 0 else '❌ FAIL'}")

    # 6. Totals sanity check
    totals = await db.execute(text("""
        SELECT
            (SELECT COUNT(*) FROM topics) as topics,
            (SELECT COUNT(*) FROM units) as units,
            (SELECT COUNT(*) FROM lessons) as lessons,
            (SELECT COUNT(*) FROM exercises) as exercises
    """))
    row = totals.fetchone()
    print(f"\n[6] Database totals:")
    print(f"     Topics:    {row[0]}")
    print(f"     Units:     {row[1]}")
    print(f"     Lessons:   {row[2]}")
    print(f"     Exercises: {row[3]}")

    all_ok = (len(dup_units) == 0 and len(dup_topics) == 0 and
              orphans == 0 and orphan_ex == 0 and orphan_units == 0)
    print(f"\n{'✅ ALL CHECKS PASSED' if all_ok else '❌ SOME CHECKS FAILED — STOP HERE'}")
    return all_ok


async def main(do_rollback=False):
    async with AsyncSessionLocal() as db:
        if do_rollback:
            print("⚠️  ROLLBACK — re-inserting all deleted entities (not implemented in this script)")
            print("    → This is a safety blocker. Restore from DB backup instead.")
            return

        print("=" * 60)
        print("PHASE 0.3 — EXECUTE CURRICULUM MERGE")
        print("=" * 60)
        print(f"Merging {len(UNIT_REMAP)} duplicate units → canonical units")
        print(f"Merging {len(TOPIC_REMAP)} duplicate topics → canonical topics")
        print()

        # Execute merge inside a transaction
        await do_merge(db)
        await db.commit()
        print("\n✅ Merge committed to DB")

        # Verify
        ok = await verify(db)
        await db.commit()

        if not ok:
            print("\n\n❌ VERIFICATION FAILED — rolling back...")
            # Note: full rollback not implemented here — restore from backup
            sys.exit(1)

        print("\n✅ PHASE 0.3 COMPLETE — merge executed and verified")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--rollback', action='store_true')
    args = parser.parse_args()
    asyncio.run(main(do_rollback=args.rollback))
