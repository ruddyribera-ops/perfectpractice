"""
Fix duplicate lesson title: rename lesson 195 to 'Práctica'
"""
import sys, asyncio
sys.path.insert(0, '/app')
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def main():
    async with AsyncSessionLocal() as db:
        print("Renaming lesson 195...")
        r = await db.execute(text("""
            UPDATE lessons SET title = 'Práctica' WHERE id = 195 RETURNING id, title, unit_id
        """))
        row = r.fetchone()
        print(f"  ✅ Renamed: id={row[0]}, title='{row[1]}', unit_id={row[2]}")
        await db.commit()
        print("Done!")

asyncio.run(main())