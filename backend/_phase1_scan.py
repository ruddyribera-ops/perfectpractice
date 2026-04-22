"""
PHASE 1.1 — Scan curriculum seed and DB for garbage content.
Reports exact locations.
"""
import re, asyncio, sys, os

print("=" * 60)
print("PHASE 1.1 — CONTENT SCAN")
print("=" * 60)

# ─── Part 1: Scan seed file ────────────────────────────────────────────────
seed_path = "/app/seed/curriculum_seed.py"
if os.path.exists(seed_path):
    with open(seed_path, "r", encoding="utf-8") as f:
        seed_content = f.read()
    print(f"\n[1] Seed file scanned: {len(seed_content)} chars")
else:
    print("  ⚠️  Seed file not found")
    seed_content = ""

# Chinese characters
chinese_re = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf\U00020000-\U0002A6DF]")
chinese_in_seed = chinese_re.findall(seed_content)
print(f"  [A] Chinese chars in seed: {len(chinese_in_seed)}")
if chinese_in_seed:
    lines = seed_content.split("\n")
    for i, line in enumerate(lines, 1):
        if chinese_re.search(line):
            m = chinese_re.search(line)
            pos = m.start()
            ctx = line[max(0, pos-15):pos+30]
            print(f"     L{i}: ...{ctx}...")

# Cyrillic words
cyrillic_re = re.compile(r"\b(десяток|работа|ученик|студент|преподаватель|школа|вычитание|сложение)\b", re.IGNORECASE)
cyrillic_in_seed = cyrillic_re.findall(seed_content)
print(f"\n  [B] Cyrillic words in seed: {len(cyrillic_in_seed)}")
if cyrillic_in_seed:
    lines = seed_content.split("\n")
    for i, line in enumerate(lines, 1):
        if cyrillic_re.search(line):
            print(f"     L{i}: {line[:120]}")

# Generic English contexts
generic_re = re.compile(
    r"\b(Alice|Bob|John|Mary|Tom)\b.*?\b(bought|went|has|had)\b.*?(apples|town|store|books)\b",
    re.IGNORECASE
)
generic_in_seed = generic_re.findall(seed_content)
print(f"\n  [C] Generic English contexts in seed: {len(generic_in_seed)}")
if generic_in_seed:
    lines = seed_content.split("\n")
    for i, line in enumerate(lines, 1):
        if generic_re.search(line):
            print(f"     L{i}: {line[:120]}")

# Specific garbled phrases found in audit
garbled = ["那我们就可以数到", "玩具", "我们可以数到", "分组", "ello puedes",
           "我们现在", "una página", "das plantas", " ученик", "десяток"]
print(f"\n  [D] Known garbled phrases in seed:")
for phrase in garbled:
    if phrase in seed_content:
        lines = seed_content.split("\n")
        for i, line in enumerate(lines, 1):
            if phrase in line:
                print(f"     L{i}: {line[:120]}")

# Spanish mixed with Chinese (the "，那我们就可以数到 **20** 了" pattern)
mixed_re = re.compile(r"那.*?(可以|我们|数到|了)\b")
mixed_in_seed = mixed_re.findall(seed_content)
print(f"\n  [E] Mixed Chinese-Spanish in seed: {len(mixed_in_seed)}")
if mixed_in_seed:
    lines = seed_content.split("\n")
    for i, line in enumerate(lines, 1):
        if mixed_re.search(line):
            print(f"     L{i}: {line[:120]}")

# ─── Part 2: Scan live DB lessons and exercises ───────────────────────────
print("\n[2] Scanning live database...")

sys.path.insert(0, "/app")
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def scan_db():
    async with AsyncSessionLocal() as db:
        # Fetch all lesson content and check in Python
        r = await db.execute(text("SELECT id, title, content FROM lessons"))
        lessons = r.fetchall()

        lessons_with_issues = []
        for row in lessons:
            lid, title, content = row
            if not content:
                continue
            chinese = chinese_re.findall(content)
            cyrillic = cyrillic_re.findall(content)
            garb = [p for p in garbled if p in content]
            mixed = mixed_re.findall(content)
            if chinese or cyrillic or garb or mixed:
                lessons_with_issues.append({
                    "id": lid, "title": title, "chinese": chinese,
                    "cyrillic": cyrillic, "garbled": garb, "mixed": mixed,
                    "preview": content[:150].replace("\n", " ")
                })

        print(f"\n  [DB] Lessons with issues: {len(lessons_with_issues)}")
        for item in lessons_with_issues:
            print(f"   Lesson id={item['id']}, title='{item['title']}'")
            if item['chinese']: print(f"     Chinese: {item['chinese'][:5]}")
            if item['cyrillic']: print(f"     Cyrillic: {item['cyrillic'][:5]}")
            if item['garbled']: print(f"     Garbled: {item['garbled']}")
            if item['mixed']: print(f"     Mixed: {item['mixed'][:3]}")
            print(f"     Preview: {item['preview'][:100]}")

        # Fetch exercise data
        r2 = await db.execute(text("SELECT id, title, data FROM exercises LIMIT 500"))
        exercises = r2.fetchall()

        exercises_with_issues = []
        for row in exercises:
            eid, title, data = row
            if not data:
                continue
            data_str = str(data)
            chinese = chinese_re.findall(data_str)
            if chinese:
                exercises_with_issues.append({"id": eid, "title": title, "chinese": chinese})

        print(f"\n  [DB] Exercises with Chinese chars: {len(exercises_with_issues)}")
        for item in exercises_with_issues[:10]:
            print(f"   Exercise id={item['id']}, title='{item['title']}': {item['chinese'][:3]}")

asyncio.run(scan_db())

print("\n" + "=" * 60)
print("SCAN COMPLETE")
print("=" * 60)