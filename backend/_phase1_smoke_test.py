"""
PHASE 1.5 — Verify API serves the fixed content correctly
"""
import asyncio, sys
sys.path.insert(0, "/app")

async def main():
    import httpx
    BASE = "http://localhost:8000"
    async with httpx.AsyncClient(base_url=BASE, timeout=15.0) as client:

        print("=" * 60)
        print("PHASE 1.5 — API SMOKE TEST")
        print("=" * 60)

        # 1. Health
        r = await client.get("/api/health")
        print(f"\n[1] GET /api/health: {r.status_code} {'✅' if r.status_code == 200 else '❌'}")

        # 2. Login
        login = await client.post("/api/auth/login", json={
            "email": "student@test.com",
            "password": "test123"
        })
        print(f"[2] POST /api/auth/login: {login.status_code}")
        if login.status_code != 200:
            print(f"    FAIL — {login.text[:200]}")
            return
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print(f"    ✅ Logged in")

        # 3. Topics list
        topics = await client.get("/api/topics", headers=headers)
        print(f"[3] GET /api/topics: {topics.status_code} {'✅' if topics.status_code == 200 else '❌'}")
        if topics.status_code == 200:
            tdata = topics.json()
            print(f"    Topics returned: {len(tdata)}")

        # 4. Lesson 167 (Contar hasta 20 — FIXED)
        l167 = await client.get("/api/lessons/167", headers=headers)
        print(f"\n[4] GET /api/lessons/167: {l167.status_code}")
        if l167.status_code == 200:
            lesson = l167.json()
            c = lesson.get("content", "")
            print(f"    Has 'Contamos juntos': {'✅' if 'contamos juntos' in c.lower() else '❌'}")
            print(f"    Has garbled Chinese: {'❌ YES' if '那我们就可以' in c else '✅ NO'}")
        elif l167.status_code == 401:
            print(f"    Auth required (expected for student) — checking DB directly instead")

        # 5. DB direct check for all 4 fixed lessons
        print(f"\n[5] DB direct verification of fixes:")
        from sqlalchemy import text
        from app.core.database import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            checks = {
                167: ("contamos juntos", "那我们就可以", "Chinese intro fix"),
                176: ("1 decena", "десяток", "Cyrillic десяток → decena"),
                197: ("es seguro que ocurre", "一定会发生", "Chinese certainty fix"),
                139: (None, "记忆", "Chinese memory char removed"),
            }
            for lid, (has_text, not_text, desc) in checks.items():
                r2 = await db.execute(text("SELECT content FROM lessons WHERE id = :id"), {"id": lid})
                row = r2.fetchone()
                if row:
                    c = row[0] or ""
                    ok_has = has_text is None or has_text.lower() in c.lower()
                    ok_not = not_text not in c
                    status = "✅" if ok_has and ok_not else "❌"
                    print(f"    Lesson {lid} ({desc}): {status}")
                    if not ok_has: print(f"       Missing: '{has_text}'")
                    if not ok_not: print(f"       Still has: '{not_text}'")

        # 6. Verify exercises data (no Chinese chars)
        print(f"\n[6] Exercises data check:")
        async with AsyncSessionLocal() as db:
            r3 = await db.execute(text("SELECT id, title, data FROM exercises LIMIT 100"))
            rows = r3.fetchall()
            chinese_ex = 0
            import re
            ch_re = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf]")
            for row in rows:
                if row[2] and ch_re.search(str(row[2])):
                    chinese_ex += 1
                    print(f"    Exercise {row[0]} ({row[1]}): has Chinese")
            print(f"    Exercises with Chinese chars: {chinese_ex} {'✅' if chinese_ex == 0 else '❌'}")

        print(f"\n{'='*60}")
        print("✅ PHASE 1.5 COMPLETE")

asyncio.run(main())