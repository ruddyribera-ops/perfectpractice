from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from datetime import date, datetime
import secrets

from app.core.database import get_db
from app.core.security import get_current_user_required
from app.models.user import User, Student, UserRole
from app.models.parent import (
    Parent, ParentStudentLink,
    ParentActivity as PAOrm, ParentActivityCompletion as PACOrm,
)
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
    parent_streak: int = 0  # consecutive days parent engaged
    parent_last_engaged_at: str | None = None
    model_config = {"from_attributes": True}


class ParentActivity(BaseModel):
    id: int
    grade: int
    title: str
    description: str
    materials: str
    estimated_minutes: int
    difficulty: str
    bar_model_topic: str | None
    topic_id: int | None
    day_index: int
    already_completed: bool = False
    model_config = {"from_attributes": True}


class ParentDashboardResponse(BaseModel):
    parent_name: str
    linked_students: list[LinkedStudent]
    daily_activity: ParentActivity | None = None
    student_id: int | None = None  # which student the activity is for


class GenerateLinkCodeResponse(BaseModel):
    link_code: str


class CompleteActivityRequest(BaseModel):
    student_id: int


class CompleteActivityResponse(BaseModel):
    success: bool
    parent_streak: int
    message: str


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
    # XP comes directly from Student.total_xp (not from StudentTopicProgress)
    xp_total = student.total_xp or 0

    # Exercises completed — sum across all topic progress
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

    # Parent engagement streak: consecutive days parent marked an activity complete
    parent_last = student.parent_last_engaged_at
    parent_streak = 0
    if parent_last:
        days_since = (date.today() - parent_last.date()).days
        if days_since <= 1:
            parent_streak = getattr(student, 'parent_participation_streak', 0) or 0

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
        "parent_streak": parent_streak,
        "parent_last_engaged_at": parent_last.isoformat() if parent_last else None,
    }


# ─── Endpoints ────────────────────────────────────────────────────────────

@router.get("/me", response_model=ParentDashboardResponse)
async def get_parent_dashboard(
    user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db),
):
    """Get parent dashboard with all linked students + today's activity."""
    if user.role != UserRole.parent:
        raise HTTPException(status_code=403, detail="Only parents can access this")

    parent = await _get_or_create_parent(db, user)

    links_result = await db.execute(
        select(ParentStudentLink, Student)
        .join(Student, ParentStudentLink.student_id == Student.id)
        .options(selectinload(Student.user))
        .where(ParentStudentLink.parent_id == parent.id)
    )

    students = []
    first_student_id = None
    first_student_grade = 1
    for (link, student) in links_result.all():
        stats = await _get_student_stats(db, student)
        students.append(LinkedStudent(**stats))
        if first_student_id is None:
            first_student_id = student.id
            first_student_grade = student.grade or 1

    # Pick daily activity based on day of year % 5 for the first student's grade
    today_activity = None
    if first_student_id:
        day_index = (date.today().timetuple().tm_yday - 1) % 5  # 0-4
        grade_filter = first_student_grade

        act_result = await db.execute(
            select(PAOrm)
            .where(PAOrm.grade == grade_filter, PAOrm.day_index == day_index)
            .limit(1)
        )
        today_activity_row = act_result.scalar_one_or_none()

        if today_activity_row:
            # Check if already completed today for this student
            today_date = date.today()
            comp_result = await db.execute(
                select(PACOrm)
                .where(
                    and_(
                        PACOrm.parent_id == parent.id,
                        PACOrm.student_id == first_student_id,
                        PACOrm.activity_id == today_activity_row.id,
                    )
                )
            )
            already_done = comp_result.first() is not None

            today_activity = ParentActivity(
                id=today_activity_row.id,
                grade=today_activity_row.grade,
                title=today_activity_row.title,
                description=today_activity_row.description,
                materials=today_activity_row.materials,
                estimated_minutes=today_activity_row.estimated_minutes,
                difficulty=today_activity_row.difficulty,
                bar_model_topic=today_activity_row.bar_model_topic,
                topic_id=today_activity_row.topic_id,
                day_index=today_activity_row.day_index,
                already_completed=already_done,
            )

    return ParentDashboardResponse(
        parent_name=user.name,
        linked_students=students,
        daily_activity=today_activity,
        student_id=first_student_id,
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


@router.post("/activities/{activity_id}/complete", response_model=CompleteActivityResponse)
async def complete_activity(
    activity_id: int,
    data: CompleteActivityRequest,
    user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db),
):
    """Mark a parent activity as complete. Updates parent engagement streak."""
    if user.role != UserRole.parent:
        raise HTTPException(status_code=403, detail="Only parents can access this")

    parent = await _get_or_create_parent(db, user)
    student_id = data.student_id

    # Verify this student is linked to this parent
    link_result = await db.execute(
        select(ParentStudentLink).where(
            and_(
                ParentStudentLink.parent_id == parent.id,
                ParentStudentLink.student_id == student_id,
            )
        )
    )
    if not link_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Estudiante no vinculado")

    # Get the student
    student_result = await db.execute(select(Student).where(Student.id == student_id))
    student = student_result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")

    # Check if already completed
    existing = await db.execute(
        select(PACOrm).where(
            and_(
                PACOrm.parent_id == parent.id,
                PACOrm.activity_id == activity_id,
                PACOrm.student_id == student_id,
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Actividad ya completada")

    # Record completion
    completion = PACOrm(
        parent_id=parent.id,
        activity_id=activity_id,
        student_id=student_id,
    )
    db.add(completion)

    # Update parent engagement streak
    today = date.today()
    if student.parent_last_engaged_at:
        days_since = (today - student.parent_last_engaged_at.date()).days
        if days_since == 1:
            student.parent_participation_streak = (student.parent_participation_streak or 0) + 1
        elif days_since > 1:
            student.parent_participation_streak = 1
        # if days_since == 0, don't change streak
    else:
        student.parent_participation_streak = 1

    student.parent_last_engaged_at = datetime.utcnow()

    await db.commit()
    await db.refresh(student)

    return CompleteActivityResponse(
        success=True,
        parent_streak=student.parent_participation_streak or 0,
        message=f"¡Actividad '{data.student_id}' marcada como completa! 🔥",
    )