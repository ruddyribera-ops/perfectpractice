"""
PHASE 1.2 — Fix garbage content in live DB lessons
4 lessons have Chinese/Cyrillic that needs cleaning.
"""
import asyncio, sys
sys.path.insert(0, "/app")
from sqlalchemy import text
from app.core.database import AsyncSessionLocal


async def main():
    async with AsyncSessionLocal() as db:
        print("=" * 60)
        print("PHASE 1.2 — FIX DB CONTENT")
        print("=" * 60)

        # Fix 1: Lesson 139 — PEMDAS — remove "记忆" (Chinese "memory" char)
        print("\n[Fix 1] Lesson 139 — remove '记忆' from PEMDAS section")
        r = await db.execute(text("""
            UPDATE lessons
            SET content = REPLACE(content, '🧠记忆 **PEMDAS**', '🧠 Repetimos **PEMDAS**')
            WHERE id = 139
            RETURNING id
        """))
        print(f"  Rows affected: {r.rowcount}")

        # Fix 2: Lesson 176 — Suma llevando — "десяток" → "decena"
        print("\n[Fix 2] Lesson 176 — replace Cyrillic 'десяток' with 'decena'")
        r = await db.execute(text("""
            UPDATE lessons
            SET content = REPLACE(content, '1 десяток', '1 decena')
            WHERE id = 176
            RETURNING id
        """))
        print(f"  Rows affected: {r.rowcount}")

        # Fix 3: Lesson 167 — Contar hasta 20 — full replacement of garbled Chinese
        print("\n[Fix 3] Lesson 167 — replace garbled Chinese intro")
        r = await db.execute(text("""
            UPDATE lessons
            SET content = REPLACE(content,
                'Ahora，那我们就可以数到 **20** 了！',
                '¡Contamos juntos hasta **20**!')
            WHERE id = 167
            RETURNING id
        """))
        print(f"  Rows affected: {r.rowcount}")

        # Fix 3b: Lesson 167 — replace "玩具" in tryit
        r = await db.execute(text("""
            UPDATE lessons
            SET content = REPLACE(content,
                '1 grupo de 10 y 4玩具, ¿cuántos玩具',
                '1 grupo de 10 y 4 objetos, ¿cuántos objetos')
            WHERE id = 167
            RETURNING id
        """))
        print(f"  Fix 3b (toy→objetos): {r.rowcount} rows")

        # Fix 4: Lesson 197 — "一定会发生" → "es seguro que ocurre"
        print("\n[Fix 4] Lesson 197 — replace Chinese certainty phrase")
        r = await db.execute(text("""
            UPDATE lessons
            SET content = REPLACE(content,
                '**Seguro** =一定会发生 (muy probable)',
                '**Seguro** = es seguro que ocurre (muy probable)')
            WHERE id = 197
            RETURNING id
        """))
        print(f"  Rows affected: {r.rowcount}")

        await db.commit()
        print("\n✅ All committed!")

        # ─── VERIFY ────────────────────────────────────────────
        print("\n[VERIFY] Re-scanning DB for issues...")
        import re
        chinese_re = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf]")
        cyrillic_re = re.compile(r"\b(десяток|работа|ученик)\b", re.IGNORECASE)
        garbled_phrases = ["那我们就可以数到", "玩具", "一定会发生", "记忆"]

        r = await db.execute(text("SELECT id, title, content FROM lessons WHERE id IN (139, 167, 176, 197)"))
        for row in r.fetchall():
            lid, title, content = row
            chinese = chinese_re.findall(content or "")
            cyrillic = cyrillic_re.findall(content or "")
            garb = [p for p in garbled_phrases if p in (content or "")]
            status = "✅ CLEAN" if not (chinese or cyrillic or garb) else f"❌ STILL HAS: {chinese or cyrillic or garb}"
            print(f"  Lesson {lid} ({title}): {status}")

asyncio.run(main())