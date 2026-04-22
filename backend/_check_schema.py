"""Check actual column names for topics, units, lessons tables"""
import sys, asyncio
sys.path.insert(0, '/app')
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def main():
    async with AsyncSessionLocal() as db:
        for table in ['topics', 'units', 'lessons']:
            r = await db.execute(text(f"""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = '{table}'
                ORDER BY ordinal_position
            """))
            cols = [row[0] for row in r.fetchall()]
            print(f"{table}: {cols}")

        # Also check sample data to understand ordering
        print("\n--- topics sample ---")
        r = await db.execute(text("SELECT id, title FROM topics ORDER BY id LIMIT 5"))
        for row in r.fetchall(): print(f"  id={row[0]}: {row[1]}")

        print("\n--- units sample (topic_id=98) ---")
        r = await db.execute(text("SELECT id, title FROM units WHERE topic_id = 98 ORDER BY id LIMIT 5"))
        for row in r.fetchall(): print(f"  id={row[0]}: {row[1]}")

        print("\n--- lessons sample (unit_id=127) ---")
        r = await db.execute(text("SELECT id, title FROM lessons WHERE unit_id = 127 ORDER BY id LIMIT 5"))
        for row in r.fetchall(): print(f"  id={row[0]}: {row[1]}")

asyncio.run(main())