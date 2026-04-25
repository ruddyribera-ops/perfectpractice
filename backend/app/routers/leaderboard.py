from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import get_current_user_required
from app.core.redis import get_redis
from app.models.user import User, Student
from app.schemas.leaderboard import LeaderboardEntry, LeaderboardMeResponse

router = APIRouter()


@router.get("/global", response_model=list[LeaderboardEntry])
async def get_global_leaderboard(
    period: str = Query("weekly", enum=["weekly", "monthly", "all_time"]),
    limit: int = Query(50, le=100),
    db: AsyncSession = Depends(get_db),
):
    redis = await get_redis()
    key = f"leaderboard:global:{period}"
    leaderboard = []

    # Try Redis first, fall back to DB
    if redis:
        try:
            entries = await redis.zrevrange(key, 0, limit - 1, withscores=True)
            for rank, (student_id_str, points) in enumerate(entries, 1):
                student_id = int(student_id_str)
                result = await db.execute(
                    select(Student).where(Student.id == student_id).options(selectinload(Student.user))
                )
                student = result.scalar_one_or_none()
                if student:
                    leaderboard.append(LeaderboardEntry(
                        rank=rank,
                        student_id=student.id,
                        student_name=student.user.name,
                        points=int(points),
                        avatar_url=student.avatar_url,
                        level=student.level,
                    ))
            return leaderboard
        except Exception:
            pass  # Redis unavailable — fall through to DB query

    # Fallback: query DB ordered by total_xp
    result = await db.execute(
        select(Student).options(selectinload(Student.user))
        .order_by(Student.total_xp.desc())
        .limit(limit)
    )
    students = result.scalars().all()
    for rank, student in enumerate(students, 1):
        leaderboard.append(LeaderboardEntry(
            rank=rank,
            student_id=student.id,
            student_name=student.user.name,
            points=student.total_xp,
            avatar_url=student.avatar_url,
            level=student.level,
        ))
    return leaderboard


@router.get("/me", response_model=LeaderboardMeResponse)
async def get_my_leaderboard_position(
    user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db),
):
    """Returns current student's rank in all three periods."""
    if user.role != "student":
        raise HTTPException(status_code=403, detail="Student only")

    student = await _get_student(db, user.id)
    redis = await get_redis()

    periods = ["weekly", "monthly", "all_time"]
    result = {}

    if redis:
        try:
            for period in periods:
                key = f"leaderboard:global:{period}"
                rank = await redis.zrevrank(key, student.id)
                score = await redis.zscore(key, student.id)
                result[period] = {
                    "rank": (rank + 1) if rank is not None else None,
                    "points": int(score) if score is not None else 0,
                }
        except Exception:
            redis = None  # Force fallback

    if not redis:
        # Fallback: use total_xp from DB
        for period in periods:
            # Count students with more XP for ranking
            rank_result = await db.execute(
                select(Student.id).where(Student.total_xp > student.total_xp)
            )
            rank = len(rank_result.scalars().all())
            result[period] = {
                "rank": rank + 1,
                "points": student.total_xp,
            }

    return LeaderboardMeResponse(
        student_id=student.id,
        name=student.user.name,
        weekly_rank=result["weekly"]["rank"],
        weekly_points=result["weekly"]["points"],
        monthly_rank=result["monthly"]["rank"],
        monthly_points=result["monthly"]["points"],
        all_time_rank=result["all_time"]["rank"],
        all_time_points=result["all_time"]["points"],
    )


async def _get_student(db: AsyncSession, user_id: int) -> Student:
    result = await db.execute(select(Student).where(Student.user_id == user_id))
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")
    return student


from fastapi import HTTPException
