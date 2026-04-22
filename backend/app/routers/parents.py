from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import secrets

from app.core.database import get_db
from app.core.security import get_current_user_required
from app.models.user import User, Student, UserRole
from app.models.parent import Parent, ParentStudentLink
from app.models.progress import StudentTopicProgress
from pydantic import BaseModel

router = APIRouter()


# ─── Schemas ────────────────────────────────────────────────────────────────

class LinkedStudent(BaseModel):
    id: int
    name: str
    grade: int
    xp_total: int
    current_streak: int
    avg_mastery: float
    exercises_completed: int
    total_exercises: int
    completion_rate: float
    model_config = {"from_attributes": True}


class ParentDashboardResponse(BaseModel):
    parent_name: str
    linked_students: list[LinkedStudent]


class GenerateLinkCodeResponse(BaseModel):
    link_code: str


# ─── Helpers ──────────────────────────────────────────────────────────────

async def _get_or_create_parent(db: AsyncSession, user: User) -> Parent:
    result = await db.execute(select(Parent).where(Parent.user_id == user.id))
    parent = result.scalar_one_or_none()
    if not parent:
        parent = Parent(user_id=user.id)
        db.add(parent)
        await db.commit()
        await db.refresh(parent)
    return parent


async def _get_student_stats(db: AsyncSession, student: Student) -> dict:
    # XP
    xp_result = await db.execute(
        select(func.sum(StudentTopicProgress.xp_total))
        .where(StudentTopicProgress.student_id == student.id)
    )
    xp_total = xp_result.scalar() or 0

    # Exercises completed
    ex_result = await db.execute(
        select(func.sum(StudentTopicProgress.exercises_completed))
        .where(StudentTopicProgress.student_id == student.id)
    )
    exercises_completed = ex_result.scalar() or 0

    # Avg mastery
    mastery_result = await db.execute(
        select(func.avg(StudentTopicProgress.mastery_score))
        .where(StudentTopicProgress.student_id == student.id)
    )
    avg_mastery = round(mastery_result.scalar() or 0.0, 1)

    # Total exercises
    total_result = await db.execute(
        select(func.sum(StudentTopicProgress.total_exercises))
        .where(StudentTopicProgress.student_id == student.id)
    )
    total_exercises = total_result.scalar() or 0

    completion_rate = round((exercises_completed / total_exercises * 100), 1) if total_exercises > 0 else 0.0

    return {
        "id": student.id,
        "name": student.user.name,
        "grade": student.grade,
        "xp_total": xp_total,
        "current_streak": student.current_streak,
        "avg_mastery": avg_mastery,
        "exercises_completed": exercises_completed,
        "total_exercises": total_exercises,
        "completion_rate": completion_rate,
    }


# ─── Endpoints ────────────────────────────────────────────────────────────

@router.get("/me", response_model=ParentDashboardResponse)
async def get_parent_dashboard(
    user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db),
):
    """Get parent dashboard with all linked students."""
    if user.role != UserRole.parent:
        raise HTTPException(status_code=403, detail="Only parents can access this")

    parent = await _get_or_create_parent(db, user)

    links_result = await db.execute(
        select(ParentStudentLink, Student)
        .join(Student, ParentStudentLink.student_id == Student.id)
        .where(ParentStudentLink.parent_id == parent.id)
    )

    students = []
    for (link, student) in links_result.all():
        stats = await _get_student_stats(db, student)
        students.append(LinkedStudent(**stats))

    return ParentDashboardResponse(
        parent_name=user.name,
        linked_students=students,
    )


@router.post("/generate-code", response_model=GenerateLinkCodeResponse)
async def generate_link_code(
    user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db),
):
    """Generate a 6-char code the parent can share with their student."""
    if user.role != UserRole.parent:
        raise HTTPException(status_code=403, detail="Only parents can access this")

    parent = await _get_or_create_parent(db, user)

    # Generate unique 6-char code
    code = secrets.token_urlsafe(6)[:6].upper()

    # Ensure unique
    while True:
        existing = await db.execute(
            select(ParentStudentLink).where(ParentStudentLink.link_code == code)
        )
        if not existing.scalar_one_or_none():
            break
        code = secrets.token_urlsafe(6)[:6].upper()

    link = ParentStudentLink(parent_id=parent.id, student_id=None, link_code=code)
    db.add(link)
    await db.commit()
    await db.refresh(link)

    return GenerateLinkCodeResponse(link_code=code)