import sys, asyncio
sys.path.insert(0, '/app')
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def scout():
    async with AsyncSessionLocal() as db:
        print("=" * 70)
        print("PHASE 0.1 — SCOUT: Duplicate Units and Topics")
        print("=" * 70)

        # 1. Exact duplicate units by title
        r = await db.execute(text("""
            SELECT title, COUNT(*) as cnt
            FROM units
            GROUP BY title
            HAVING COUNT(*) > 1
            ORDER BY cnt DESC
        """))
        dup_units = r.fetchall()
        print(f"\n[1] UNITS WITH DUPLICATE TITLES: {len(dup_units)}")
        for row in dup_units:
            print(f"  ❌ '{row[0]}' appears {row[1]} times")

        # 2. Exact duplicate topics by title
        r2 = await db.execute(text("""
            SELECT title, COUNT(*) as cnt
            FROM topics
            GROUP BY title
            HAVING COUNT(*) > 1
            ORDER BY cnt DESC
        """))
        dup_topics = r2.fetchall()
        print(f"\n[2] TOPICS WITH DUPLICATE TITLES: {len(dup_topics)}")
        for row in dup_topics:
            print(f"  ❌ '{row[0]}' appears {row[1]} times")

        # 3. For each duplicate unit, show details
        print(f"\n[3] DETAILED UNIT DUPLICATES:")
        for row in dup_units:
            title = row[0]
            r3 = await db.execute(text("""
                SELECT u.id, u.title, u.topic_id, t.title as topic_title, u.order_index,
                       (SELECT COUNT(*) FROM lessons l WHERE l.unit_id = u.id) as lesson_count,
                       (SELECT COUNT(*) FROM exercises e WHERE e.unit_id = u.id) as exercise_count
                FROM units u
                JOIN topics t ON t.id = u.topic_id
                WHERE u.title = :title
                ORDER BY exercise_count DESC
            """), {"title": title})
            units = r3.fetchall()
            for u in units:
                print(f"  📦 Unit(id={u[0]}, topic={u[3]}) title='{u[1]}' order={u[4]} lessons={u[5]} exercises={u[6]}")
            print()

        # 4. Near-duplicate units (case-insensitive — fixed GROUP BY)
        r4 = await db.execute(text("""
            SELECT LOWER(title) as lower_title, COUNT(*) as cnt
            FROM units
            GROUP BY LOWER(title)
            HAVING COUNT(*) > 1
        """))
        near_dup = r4.fetchall()
        print(f"[4] NEAR-DUPLICATE UNITS (case-insensitive): {len(near_dup)}")
        for row in near_dup:
            print(f"  ⚠️  '{row[0]}' appears {row[1]} times")

        # 5. Near-duplicate topics (case-insensitive — fixed GROUP BY)
        r5 = await db.execute(text("""
            SELECT LOWER(title) as lower_title, COUNT(*) as cnt
            FROM topics
            GROUP BY LOWER(title)
            HAVING COUNT(*) > 1
        """))
        near_dup_topic = r5.fetchall()
        print(f"\n[5] NEAR-DUPLICATE TOPICS (case-insensitive): {len(near_dup_topic)}")
        for row in near_dup_topic:
            print(f"  ⚠️  '{row[0]}' appears {row[1]} times")

        # 6. All topics with unit count
        r6 = await db.execute(text("""
            SELECT t.title, t.id,
                   (SELECT COUNT(*) FROM units u WHERE u.topic_id = t.id) as unit_count,
                   (SELECT COUNT(*) FROM lessons l WHERE l.unit_id IN (SELECT id FROM units WHERE topic_id = t.id)) as lesson_count
            FROM topics t
            ORDER BY t.title
        """))
        all_topics = r6.fetchall()
        print(f"\n[6] ALL TOPICS ({len(all_topics)} total):")
        for row in all_topics:
            print(f"  📚 Topic '{row[0]}' (id={row[1]}) units={row[2]} lessons={row[3]}")

        # 7. Duplicate lessons within same unit
        r7 = await db.execute(text("""
            SELECT l.title, l.unit_id, u.title as unit_title, COUNT(*) as cnt
            FROM lessons l
            JOIN units u ON u.id = l.unit_id
            GROUP BY l.title, l.unit_id, u.title
            HAVING COUNT(*) > 1
            ORDER BY cnt DESC
        """))
        dup_lessons = r7.fetchall()
        print(f"\n[7] LESSONS WITH DUPLICATE TITLES IN SAME UNIT: {len(dup_lessons)}")
        for row in dup_lessons:
            print(f"  ❌ '{row[0]}' in unit '{row[2]}' appears {row[3]} times")

        # 8. Summary counts
        total_units = await db.execute(text("SELECT COUNT(*) FROM units"))
        total_topics = await db.execute(text("SELECT COUNT(*) FROM topics"))
        total_lessons = await db.execute(text("SELECT COUNT(*) FROM lessons"))
        total_exercises = await db.execute(text("SELECT COUNT(*) FROM exercises"))

        print(f"\n[8] DATABASE TOTALS:")
        print(f"  Topics:    {total_topics.scalar()}")
        print(f"  Units:     {total_units.scalar()}")
        print(f"  Lessons:   {total_lessons.scalar()}")
        print(f"  Exercises: {total_exercises.scalar()}")

        print("\n" + "=" * 70)
        print("SCOUT COMPLETE")
        print("=" * 70)

asyncio.run(scout())
