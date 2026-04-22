"""Check DB lesson content for the 4 problematic lessons"""
import asyncio, sys
sys.path.insert(0, "/app")
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def main():
    async with AsyncSessionLocal() as db:
        for lid in [139, 176, 167, 197]:
            r = await db.execute(text("SELECT id, title, content FROM lessons WHERE id = :id"), {"id": lid})
            row = r.fetchone()
            if row:
                print(f"\n=== Lesson {lid}: {row[1]} ===")
                print(row[2][:500] if row[2] else "EMPTY")

asyncio.run(main())