"""Direct DB check for specific tryit blocks"""
import asyncio, sys, re
sys.path.insert(0, "/app")
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def main():
    async with AsyncSessionLocal() as db:
        # Check Lesson 176 (Suma llevando) tryit blocks directly
        r = await db.execute(text("SELECT id, title, content FROM lessons WHERE id = 176"))
        row = r.fetchone()
        if row:
            content = row[2]
            # Find all tryit blocks using simple string search
            idx = 0
            blocks = []
            while True:
                start = content.find(":::tryit:", idx)
                if start == -1:
                    break
                end = content.find(":::", start + 9)
                if end == -1:
                    break
                block = content[start+9:end]
                blocks.append(block)
                idx = end + 3

            print(f"Lesson 176 (Suma llevando) — {len(blocks)} tryit blocks:")
            for i, b in enumerate(blocks):
                parts = b.split("|")
                print(f"  Block {i+1}:")
                print(f"    Q ({len(parts[0])} chars): {parts[0][:80]}")
                print(f"    A ({len(parts[1]) if len(parts)>1 else 0} chars): {parts[1][:40] if len(parts)>1 else 'MISSING'}")
                print(f"    HINT ({len(parts[2]) if len(parts)>2 else 0} chars): {parts[2][:60] if len(parts)>2 else 'MISSING'}")

        # Also check lesson 167
        r2 = await db.execute(text("SELECT id, title, content FROM lessons WHERE id = 167"))
        row2 = r2.fetchone()
        if row2:
            content = row2[2]
            idx = 0
            blocks = []
            while True:
                start = content.find(":::tryit:", idx)
                if start == -1:
                    break
                end = content.find(":::", start + 9)
                if end == -1:
                    break
                block = content[start+9:end]
                blocks.append(block)
                idx = end + 3

            print(f"\nLesson 167 (Contar hasta 20) — {len(blocks)} tryit blocks:")
            for i, b in enumerate(blocks):
                parts = b.split("|")
                print(f"  Block {i+1}:")
                print(f"    Q: {parts[0][:80]}")
                print(f"    A: {parts[1][:40] if len(parts)>1 else 'MISSING'}")

asyncio.run(main())