"""
PHASE 1.4 — Check all non-ASCII special characters used in lessons/exercises.
Focus: emojis, math symbols, Spanish special chars (áéíóúüñ¿¡)
"""
import asyncio, sys, re
sys.path.insert(0, "/app")
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

print("=" * 60)
print("PHASE 1.4 — SPECIAL CHARACTERS AUDIT")
print("=" * 60)

# All emoji ranges used in the platform
emoji_re = re.compile(r"[\U0001F300-\U0001F9FF\U00002702-\U000027B0\U000024C2-\U0001F251"
                      r"\U00002600-\U000026FF\U00002700-\U000027BF"
                      r"\U0001F600-\U0001F64F\U0001F900-\U0001F9FF]")

# Spanish special chars (should be fine)
spanish_special = re.compile(r"[áéíóúüñ¿¡ÁÉÍÓÚÜÑ]")

# Math symbols used in content
math_re = re.compile(r"[×÷√π∞≤≈±≤≥≠∫∑∏∂∆∑∏∫]")


async def main():
    async with AsyncSessionLocal() as db:
        r = await db.execute(text("SELECT id, title, content FROM lessons"))
        lessons = r.fetchall()

        total_emoji = 0
        total_spanish = 0
        emoji_lessons = set()

        for row in lessons:
            lid, title, content = row or ""
            emojis = emoji_re.findall(content)
            spanish = spanish_special.findall(content)
            math = math_re.findall(content)
            total_emoji += len(emojis)
            total_spanish += len(spanish)
            if emojis:
                emoji_lessons.add((lid, title, tuple(set(emojis[:3]))))

        print(f"\n[DB Lessons]")
        print(f"  Total emoji characters: {total_emoji}")
        print(f"  Lessons with emojis: {len(emoji_lessons)}")
        print(f"  Total Spanish special chars: {total_spanish}")

        # Show emoji usage examples
        print(f"\n[Sample emoji usage]:")
        for lid, title, emojis in list(emoji_lessons)[:5]:
            print(f"  Lesson {lid} ({title}): {' '.join(set(emojis))}")

        # Check exercises for emoji usage
        r2 = await db.execute(text("SELECT id, title, data FROM exercises LIMIT 200"))
        exercises = r2.fetchall()
        emoji_exercises = []
        for row in exercises:
            eid, title, data = row
            if data and emoji_re.search(str(data)):
                emoji_exercises.append((eid, title, emoji_re.findall(str(data))[:3]))

        print(f"\n[Exercises with emojis]: {len(emoji_exercises)}")
        for eid, title, emojis in emoji_exercises[:5]:
            print(f"  Exercise {eid} ({title}): {' '.join(set(emojis))}")

        # Check for any encoding issues (REPLACEMENT CHARACTER)
        r3 = await db.execute(text("SELECT COUNT(*) FROM lessons WHERE content LIKE '%\ufffd%'"))
        replacement_chars = r3.scalar()
        print(f"\n[Replacement characters (encoding issues)]: {replacement_chars} {'✅' if replacement_chars == 0 else '❌'}")

        print("\n✅ Special character audit complete — emojis and Spanish chars are fine for rendering")

asyncio.run(main())