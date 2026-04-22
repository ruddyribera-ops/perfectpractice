"""Investigate duplicate lesson title"""
import sys, asyncio
sys.path.insert(0, '/app')
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def main():
    async with AsyncSessionLocal() as db:
        r = await db.execute(text("""
            SELECT l.id, l.title, l.unit_id, u.title as unit_title
            FROM lessons l
            JOIN units u ON u.id = l.unit_id
            WHERE l.title = 'Fracciones equivalentes'
            ORDER BY l.id
        """))
        rows = r.fetchall()
        print("Lessons titled 'Fracciones equivalentes':")
        for row in rows:
            print(f"  id={row[0]}, unit_id={row[2]}, unit='{row[3]}'")

        # Show content of each
        for row in rows:
            lid = row[0]
            r2 = await db.execute(text("SELECT content FROM lessons WHERE id = :id"), {"id": lid})
            content = r2.fetchone()
            print(f"\n  Lesson id={lid} content preview: {content[0][:200] if content else 'N/A'}...")

asyncio.run(main())