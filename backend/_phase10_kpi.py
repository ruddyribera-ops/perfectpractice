"""
Phase 10 — KPI Monitoring Framework
Run inside the container: docker exec math-platform-backend-1 python /app/_phase10_kpi.py

KPIs defined:
  KPI 1: % of parents who complete at least 1 activity per week
  KPI 2: % of bar_model exercises solved interactively (construction JSON) vs typed answer
  KPI 3: TOP_HELPER badge award rate per week
"""
import asyncio
from datetime import date, timedelta, timezone
from sqlalchemy import text
from app.core.database import engine

async def get_kpis():
    async with engine.begin() as conn:
        today = date.today()
        week_start = today - timedelta(days=7)
        month_start = today - timedelta(days=30)

        # Inline date strings — avoids SQLAlchemy named param issues with asyncpg
        week_str = week_start.isoformat()
        month_str = month_start.isoformat()
        today_str = today.isoformat()

        print("=" * 60)
        print(f"PHASE 10 — KPI MONITORING REPORT")
        print(f"Report date: {today_str}")
        print(f"Week:       {week_str} → {today_str}")
        print(f"Month:      {month_str} → {today_str}")
        print("=" * 60)

        # ── KPI 1: Parent Participation Rate (weekly) ────────────────────────
        r1 = await conn.execute(text(f"""
            WITH active_parents AS (
                SELECT DISTINCT pac.parent_id
                FROM parent_activity_completions pac
                WHERE pac.completed_at >= '{week_str}'::timestamptz
            ),
            total_linked_parents AS (
                SELECT DISTINCT psl.parent_id
                FROM parent_student_links psl
                WHERE psl.student_id IS NOT NULL
            )
            SELECT
                COUNT(DISTINCT ap.parent_id)                   AS active_parents,
                COUNT(DISTINCT tlp.parent_id)                  AS total_linked_parents,
                CASE
                    WHEN COUNT(DISTINCT tlp.parent_id) > 0
                    THEN ROUND(
                        100.0 * COUNT(DISTINCT ap.parent_id) /
                        COUNT(DISTINCT tlp.parent_id), 1)
                    ELSE 0
                END                                            AS participation_pct
            FROM total_linked_parents tlp
            LEFT JOIN active_parents ap ON ap.parent_id = tlp.parent_id
        """))
        row1 = r1.fetchone()
        active_parents = row1[0] if row1 else 0
        total_parents = row1[1] if row1 else 0
        kpi1_pct = float(row1[2]) if row1 and row1[2] is not None else 0.0

        print(f"\n📊 KPI 1 — Parent Activity Completion Rate (weekly)")
        print(f"   Active parents (≥1 activity): {active_parents}")
        print(f"   Total linked parents:          {total_parents}")
        print(f"   Participation rate:            {kpi1_pct}%")
        print(f"   Target:                        ≥50%")
        print(f"   Status:                         {'✅ ON TRACK' if kpi1_pct >= 50 else '⚠️  BELOW TARGET'}")

        # ── KPI 2: Bar Model Interactivity Rate ────────────────────────────
        r2 = await conn.execute(text(f"""
            WITH bar_attempts AS (
                SELECT
                    ea.id,
                    ea.answer_json,
                    CASE
                        WHEN ea.answer_json IS NOT NULL
                             AND (ea.answer_json->>'type') = 'bar_model_construction'
                             AND (ea.answer_json->>'segments_built') IS NOT NULL
                        THEN 1 ELSE 0
                    END AS is_interactive
                FROM exercise_attempts ea
                JOIN exercises e ON e.id = ea.exercise_id
                WHERE e.exercise_type = 'bar_model'
                  AND ea.attempted_at >= '{month_str}'::timestamptz
            )
            SELECT
                COUNT(*)                           AS total_bar_attempts,
                COALESCE(SUM(is_interactive), 0)    AS interactive_attempts,
                CASE
                    WHEN COUNT(*) > 0
                    THEN ROUND(100.0 * COALESCE(SUM(is_interactive), 0) / COUNT(*), 1)
                    ELSE 0
                END                               AS interactivity_pct
            FROM bar_attempts
        """))
        row2 = r2.fetchone()
        total_bar = row2[0] if row2 else 0
        interactive_bar = int(row2[1]) if row2 else 0
        kpi2_pct = float(row2[2]) if row2 and row2[2] is not None else 0.0

        print(f"\n📊 KPI 2 — Bar Model Interactivity Rate (monthly)")
        print(f"   Interactive constructions:      {interactive_bar}")
        print(f"   Total bar_model attempts:      {total_bar}")
        print(f"   Interactivity rate:             {kpi2_pct}%")
        print(f"   Target:                        ≥60%")
        print(f"   Status:                        {'✅ ON TRACK' if kpi2_pct >= 60 else '⚠️  BELOW TARGET'}")

        # ── KPI 3: TOP_HELPER Badge Issuance Rate ───────────────────────────
        r3 = await conn.execute(text(f"""
            WITH weekly_helpers AS (
                SELECT DISTINCT ea.student_id
                FROM exercise_attempts ea
                WHERE ea.helped_peer_id IS NOT NULL
                  AND ea.attempted_at >= '{week_str}'::timestamptz
            ),
            weekly_top_badges AS (
                SELECT DISTINCT a.student_id
                FROM achievements a
                WHERE a.badge_key = 'top-helper'
                  AND a.earned_at >= '{week_str}'::timestamptz
            )
            SELECT
                COUNT(DISTINCT wh.student_id)             AS students_who_helped,
                COUNT(DISTINCT wtb.student_id)              AS students_earned_top_helper,
                CASE
                    WHEN COUNT(DISTINCT wh.student_id) > 0
                    THEN ROUND(100.0 * COUNT(DISTINCT wtb.student_id) /
                               COUNT(DISTINCT wh.student_id), 1)
                    ELSE 0
                END                                      AS issuance_pct
            FROM weekly_helpers wh
            LEFT JOIN weekly_top_badges wtb ON wtb.student_id = wh.student_id
        """))
        row3 = r3.fetchone()
        students_helped = int(row3[0]) if row3 else 0
        badges_earned = int(row3[1]) if row3 else 0
        kpi3_pct = float(row3[2]) if row3 and row3[2] is not None else 0.0

        print(f"\n📊 KPI 3 — TOP HELPER Badge Issuance Rate (weekly)")
        print(f"   Students who helped peers:      {students_helped}")
        print(f"   Students who earned badge:     {badges_earned}")
        print(f"   Issuance rate:                  {kpi3_pct}%")
        print(f"   Target:                        ≥40%")
        print(f"   Status:                        {'✅ ON TRACK' if kpi3_pct >= 40 else '⚠️  BELOW TARGET'}")

        # ── Summary ────────────────────────────────────────────────────────
        print(f"\n{'=' * 60}")
        print(f"SUMMARY")
        print(f"{'=' * 60}")
        kpis = [
            ("KPI 1 — Parent Participation", kpi1_pct, 50),
            ("KPI 2 — Bar Model Interactivity", kpi2_pct, 60),
            ("KPI 3 — Top Helper Issuance", kpi3_pct, 40),
        ]
        for name, value, target in kpis:
            status = "✅" if value >= target else "⚠️"
            print(f"  {status} {name}: {value}% (target ≥{target}%)")

        print(f"\nNOTE: All KPIs use monthly data for bar model (KPI 2) and weekly for")
        print(f"      participation (KPI 1) and badges (KPI 3). KPIs require ≥1 week")
        print(f"      of production data before becoming meaningful.")
        print(f"{'=' * 60}")

asyncio.run(get_kpis())
