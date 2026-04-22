"""
PHASE 0.7 — Compare current DB state with seed code to find what changed.
Produces the deltas that need to be removed from curriculum_seed.py.
"""
import sys, asyncio
sys.path.insert(0, '/app')
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def main():
    async with AsyncSessionLocal() as db:
        print("=" * 60)
        print("PHASE 0.7 — SEED CODE DELTA")
        print("=" * 60)

        # Current DB topic IDs
        r = await db.execute(text("SELECT id, title FROM topics ORDER BY id"))
        db_topics = {row[0]: row[1] for row in r.fetchall()}
        print(f"\n[DB Topics] {len(db_topics)} topics, IDs: {sorted(db_topics.keys())}")

        # Current DB unit IDs
        r = await db.execute(text("SELECT id, title, topic_id FROM units ORDER BY id"))
        db_units = [(row[0], row[1], row[2]) for row in r.fetchall()]
        print(f"\n[DB Units] {len(db_units)} units, IDs: {[u[0] for u in db_units]}")

        # Current DB lesson IDs
        r = await db.execute(text("SELECT id, title, unit_id FROM lessons ORDER BY id"))
        db_lessons = [(row[0], row[1], row[2]) for row in r.fetchall()]
        print(f"\n[DB Lessons] {len(db_lessons)} lessons")

        # Removed IDs (before 0.3 dedup):
        # Topics: 78, 85, 113, 67, 118, 70, 111
        # Units: 169 (duplicate Fracciones equivalentes in topic 108)
        removed_topics = [78, 85, 113, 67, 118, 70, 111]
        removed_units = [169]
        removed_lessons = []  # none explicitly removed (lessons from unit 169 were reassigned)

        print(f"\n[REMOVED] Topics: {removed_topics}")
        print(f"[REMOVED] Units: {removed_units}")
        print(f"[REMOVED] Lessons: {removed_lessons}")

        # For each removed topic, what was its title?
        print("\n[Removed topic details]:")
        # We can't query them since they're deleted, but we know from earlier output:
        # 78: 'Fracciones', 85: 'Estadística Avanzada', 113: 'Probabilidad'
        # 67: 'Números hasta 100', 118: 'Volumen', 70: 'Medición', 111: 'Fracciones y decimales'
        removed_topic_names = {
            78: 'Fracciones', 85: 'Estadística Avanzada', 113: 'Probabilidad',
            67: 'Números hasta 100', 118: 'Volumen', 70: 'Medición', 111: 'Fracciones y decimales'
        }
        for tid, name in removed_topic_names.items():
            print(f"  Topic {tid}: '{name}'")

        print("\n[NOTE] Seed code (curriculum_seed.py) must be updated to:")
        print("  1. Remove topic entries with IDs: 78, 85, 113, 67, 118, 70, 111")
        print("  2. Remove unit entries with IDs: 169")
        print("  3. Remove any lessons that were ONLY in unit 169 (reassigned to 127)")
        print("  4. Update unit.topic_id for remapped units (78→98, 85→95, etc.)")
        print("  5. Update lesson 'Fracciones equivalentes' id=195 title → 'Práctica'")
        print(f"\n  Final canonical IDs after dedup:")
        print(f"  Topics: {sorted(db_topics.keys())}")
        print(f"  Units: {len(db_units)} units")

asyncio.run(main())