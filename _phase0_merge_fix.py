"""
PHASE 0.3 v2 — Fix FK chain: remap student_topic_progress BEFORE deleting topics
────────────────────────────────────────────────────────────────────────────────
The previous run already executed Steps 1-3 (unit remapping + deletion).
Step 4 failed at topic id=78 because student_topic_progress still references it.
This script fixes only the broken FK chain and completes Step 4.
"""
import sys, asyncio
sys.path.insert(0, '/app')
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

# student_topic_progress FK: topic_id → topics(id)
# Remap these BEFORE deleting topics
STP_REMAP = {
    # {duplicate_topic_id}: {canonical_topic_id}
    78:  98,   # Fracciones
    85:  95,   # Estadística Avanzada
    113: 110,  # Probabilidad
    67:  103,  # Números hasta 100
    118: 90,   # Volumen
    70:  102,  # Medición
    82:  108,  # Fracciones y Decimales
    111: 108,  # Fracciones y decimales (triplet merge)
}


async def main():
    async with AsyncSessionLocal() as db:
        print("=" * 60)
        print("PHASE 0.3 v2 — FIX student_topic_progress FK")
        print("=" * 60)

        print("\nSTEP 2.5 — Remap topic FKs in student_topic_progress")
        for dup_id, canon_id in STP_REMAP.items():
            r = await db.execute(text("""
                UPDATE student_topic_progress
                SET topic_id = :canon_id
                WHERE topic_id = :dup_id
                RETURNING id, student_id
            """), {"canon_id": canon_id, "dup_id": dup_id})
            rows = r.fetchall()
            print(f"  Topic {dup_id} → {canon_id}: {len(rows)} student_topic_progress rows remapped")

        print("\nSTEP 4 (remaining) — Delete duplicate topics")
        # These are the ones that failed:
        remaining = [78, 85, 113, 67, 118, 70, 82, 111]
        for dup_id in remaining:
            r = await db.execute(text("""
                DELETE FROM topics WHERE id = :id RETURNING id, title
            """), {"id": dup_id})
            deleted = r.rowcount
            print(f"  Deleted topic {dup_id}: {'OK' if deleted else 'NOT FOUND'}")

        await db.commit()
        print("\n✅ Committed!")

        # Quick verify
        r = await db.execute(text("""
            SELECT COUNT(*) FROM student_topic_progress
            WHERE topic_id NOT IN (SELECT id FROM topics)
        """))
        orphan_stp = r.scalar()
        print(f"\n[CHECK] Orphan student_topic_progress after remap: {orphan_stp} {'✅' if orphan_stp == 0 else '❌'}")

        r2 = await db.execute(text("""
            SELECT title, COUNT(*) as cnt FROM topics GROUP BY title HAVING COUNT(*) > 1
        """))
        dup_topics = r2.fetchall()
        print(f"[CHECK] Duplicate topic titles remaining: {len(dup_topics)} {'✅ NONE' if len(dup_topics) == 0 else '❌'}")
        for row in dup_topics:
            print(f"     ❌ '{row[0]}' appears {row[1]} times")

asyncio.run(main())
