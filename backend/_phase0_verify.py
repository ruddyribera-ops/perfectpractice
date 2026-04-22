"""
PHASE 0.6 — Full post-merge verification (all checks)
"""
import sys, asyncio
sys.path.insert(0, '/app')
from sqlalchemy import text
from app.core.database import AsyncSessionLocal


async def main():
    async with AsyncSessionLocal() as db:
        print("=" * 60)
        print("PHASE 0.6 — FULL POST-MERGE VERIFICATION")
        print("=" * 60)

        issues = 0

        # 1. Duplicate topic titles
        r = await db.execute(text("SELECT title, COUNT(*) FROM topics GROUP BY title HAVING COUNT(*) > 1"))
        dup_t = r.fetchall()
        print(f"\n[1] Duplicate topic titles: {len(dup_t)} {'✅ NONE' if not dup_t else '❌ FAIL'}")
        for row in dup_t: print(f"   ❌ '{row[0]}' x{row[1]}"); issues += 1

        # 2. Duplicate unit titles (same title AND same topic)
        r = await db.execute(text("""
            SELECT u.title, t.title, COUNT(*) as cnt
            FROM units u
            JOIN topics t ON t.id = u.topic_id
            GROUP BY u.title, t.title, t.id
            HAVING COUNT(*) > 1
        """))
        dup_u = r.fetchall()
        print(f"[2] Duplicate units (same title+topic): {len(dup_u)} {'✅ NONE' if not dup_u else '❌ FAIL'}")
        for row in dup_u: print(f"   ❌ '{row[0]}' x{row[1]}"); issues += 1

        # 3. Duplicate lesson titles (same title AND same unit)
        r = await db.execute(text("""
            SELECT l.title, u.title, COUNT(*) as cnt
            FROM lessons l
            JOIN units u ON u.id = l.unit_id
            GROUP BY l.title, u.title, u.id
            HAVING COUNT(*) > 1
        """))
        dup_l = r.fetchall()
        print(f"[3] Duplicate lessons (same title+unit): {len(dup_l)} {'✅ NONE' if not dup_l else '❌ FAIL'}")
        for row in dup_l: print(f"   ❌ '{row[0]}' x{row[1]}"); issues += 1

        # 4. Orphan lessons (unit_id not in units)
        r = await db.execute(text("SELECT COUNT(*) FROM lessons WHERE unit_id NOT IN (SELECT id FROM units)"))
        orphan_l = r.scalar()
        print(f"[4] Orphan lessons: {orphan_l} {'✅' if not orphan_l else '❌'}"); issues += orphan_l

        # 5. Orphan units (topic_id not in topics)
        r = await db.execute(text("SELECT COUNT(*) FROM units WHERE topic_id NOT IN (SELECT id FROM topics)"))
        orphan_u = r.scalar()
        print(f"[5] Orphan units: {orphan_u} {'✅' if not orphan_u else '❌'}"); issues += orphan_u

        # 6. Orphan exercises (unit_id not in units)
        r = await db.execute(text("SELECT COUNT(*) FROM exercises WHERE unit_id NOT IN (SELECT id FROM units)"))
        orphan_e = r.scalar()
        print(f"[6] Orphan exercises: {orphan_e} {'✅' if not orphan_e else '❌'}"); issues += orphan_e

        # 7. Duplicate unit order_index within topic
        r = await db.execute(text("""
            SELECT topic_id, order_index, COUNT(*) as cnt
            FROM units
            GROUP BY topic_id, order_index
            HAVING COUNT(*) > 1
        """))
        dup_ui = r.fetchall()
        print(f"[7] Unit order_index duplicates: {len(dup_ui)} {'✅ NONE' if not dup_ui else '❌ FAIL'}")
        issues += len(dup_ui)

        # 8. Duplicate lesson order_index within unit
        r = await db.execute(text("""
            SELECT unit_id, order_index, COUNT(*) as cnt
            FROM lessons
            GROUP BY unit_id, order_index
            HAVING COUNT(*) > 1
        """))
        dup_li = r.fetchall()
        print(f"[8] Lesson order_index duplicates: {len(dup_li)} {'✅ NONE' if not dup_li else '❌ FAIL'}")
        issues += len(dup_li)

        # 9. STP referencing non-existent topics
        r = await db.execute(text("SELECT COUNT(*) FROM student_topic_progress WHERE topic_id NOT IN (SELECT id FROM topics)"))
        orphan_stp = r.scalar()
        print(f"[9] Orphan student_topic_progress: {orphan_stp} {'✅' if not orphan_stp else '❌'}"); issues += orphan_stp

        # 10. STP referencing non-existent students
        r = await db.execute(text("SELECT COUNT(*) FROM student_topic_progress WHERE student_id NOT IN (SELECT id FROM students)"))
        orphan_stp2 = r.scalar()
        print(f"[10] STP with invalid student_id: {orphan_stp2} {'✅' if not orphan_stp2 else '❌'}"); issues += orphan_stp2

        # 11. Final totals
        totals = await db.execute(text("""
            SELECT
                (SELECT COUNT(*) FROM topics),
                (SELECT COUNT(*) FROM units),
                (SELECT COUNT(*) FROM lessons),
                (SELECT COUNT(*) FROM exercises)
        """))
        row = totals.fetchone()
        print(f"\n[11] Final totals — Topics: {row[0]}, Units: {row[1]}, Lessons: {row[2]}, Exercises: {row[3]}")

        print(f"\n{'='*60}")
        if issues == 0:
            print("✅ ALL CHECKS PASSED — Phase 0.6 COMPLETE")
            print("   Next: Phase 0.7 — Update seed code")
        else:
            print(f"❌ {issues} issue(s) found — fix before proceeding")

asyncio.run(main())