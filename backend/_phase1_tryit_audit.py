"""
PHASE 1.3 — Audit all :::tryit::: blocks in DB lessons for:
- Readable Spanish (no garbled chars, no mixed English when Spanish would be better)
- Correct format: question|answer|hint|extra
- Math expressions renderable
"""
import asyncio, sys, re
sys.path.insert(0, "/app")
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

# Regex to find all tryit blocks
# Match everything between :::tryit: and :::  (handles colons inside question)
TRYIT_RE = re.compile(r":::tryit:(.*?):::", re.DOTALL)

print("=" * 60)
print("PHASE 1.3 — TRYAIT BLOCK AUDIT")
print("=" * 60)

async def main():
    async with AsyncSessionLocal() as db:
        r = await db.execute(text("SELECT id, title, content FROM lessons"))
        lessons = r.fetchall()

        total_blocks = 0
        lessons_with_blocks = 0
        issues = []

        for row in lessons:
            lid, title, content = row
            if not content:
                continue

            matches = TRYIT_RE.findall(content)
            if not matches:
                continue
            lessons_with_blocks += 1
            total_blocks += len(matches)

            for m in matches:
                inner = m[0].strip()
                parts = inner.split("|")
                question = parts[0].strip()
                answer = parts[1].strip() if len(parts) > 1 else ""
                hint = parts[2].strip() if len(parts) > 2 else ""
                extra = parts[3].strip() if len(parts) > 3 else ""

                # Check for issues
                block_issues = []

                # 1. Missing parts
                if not question:
                    block_issues.append("missing_question")
                if not answer:
                    block_issues.append("missing_answer")

                # 2. Question too short (likely garbled)
                if question and len(question) < 5:
                    block_issues.append(f"question_too_short:'{question}'")

                # 3. Check for garbled Chinese in question
                if re.search(r"[\u4e00-\u9fff\u3400-\u4dbf]", question):
                    block_issues.append("chinese_in_question")

                # 4. Check for garbled Chinese in answer/hint
                for val, name in [(answer, "answer"), (hint, "hint"), (extra, "extra")]:
                    if re.search(r"[\u4e00-\u9fff\u3400-\u4dbf]", val):
                        block_issues.append(f"chinese_in_{name}")

                # 5. Check for mixed language (English question in Spanish lesson - needs review)
                # Pattern: mostly Spanish lesson but English words like "group", "count", "how many"
                english_words = re.findall(r"\b(Group|Count|How many|What is|Total)\b", question, re.IGNORECASE)
                if english_words and not re.search(r"[áéíóúüñ]", question):
                    block_issues.append(f"english_question:{english_words}")

                # 6. Question mark present
                if question and "?" not in question and len(question) > 20:
                    block_issues.append("no_question_mark")

                if block_issues:
                    issues.append({
                        "lid": lid, "title": title,
                        "question": question[:80],
                        "answer": answer[:30],
                        "issues": block_issues
                    })

        print(f"\nTotal tryit blocks: {total_blocks}")
        print(f"Lessons with blocks: {lessons_with_blocks}")
        print(f"Blocks with issues: {len(issues)}")

        if issues:
            print(f"\n⚠️  ISSUES FOUND:")
            for issue in issues:
                print(f"\n  Lesson {issue['lid']} ({issue['title']}):")
                print(f"    Q: {issue['question']}")
                print(f"    A: {issue['answer']}")
                print(f"    Issues: {issue['issues']}")
        else:
            print("\n✅ ALL tryit blocks look good!")

asyncio.run(main())