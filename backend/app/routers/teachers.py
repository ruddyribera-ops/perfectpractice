from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from sqlalchemy.orm import selectinload
import secrets

from app.core.database import get_db
from app.core.security import get_current_user_required
from app.models.user import User, Teacher, Student
from app.models.classes import Class, ClassEnrollment, Assignment, AssignmentExercise, StudentAssignment
from app.models.progress import StudentTopicProgress
from app.models.progress import ExerciseAttempt, StudentTopicProgress
from app.schemas.teacher import (
    ClassCreateRequest, ClassResponse, ClassStudentsResponse,
    ClassDetailResponse, AssignmentResponse, AssignmentCreateRequest,
)


router = APIRouter()


@router.post("/classes", response_model=ClassResponse)
async def create_class(
    data: ClassCreateRequest,
    user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db),
):
    if user.role not in ["teacher", "admin"]:
        raise HTTPException(status_code=403, detail="Teacher only")
    teacher = await _get_teacher(db, user.id)
    invite_code = secrets.token_urlsafe(8)
    class_ = Class(name=data.name, teacher_id=teacher.id, subject=data.subject, invite_code=invite_code)
    db.add(class_)
    await db.commit()
    await db.refresh(class_)
    return ClassResponse.model_validate(class_)


@router.get("/classes", response_model=list[ClassResponse])
async def list_my_classes(
    user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db),
):
    if user.role not in ["teacher", "admin"]:
        raise HTTPException(status_code=403, detail="Teacher only")
    teacher = await _get_teacher(db, user.id)
    result = await db.execute(select(Class).where(Class.teacher_id == teacher.id))
    classes = result.scalars().all()

    responses = []
    for c in classes:
        # Count enrolled students
        student_count_result = await db.execute(
            select(func.count(ClassEnrollment.id)).where(ClassEnrollment.class_id == c.id)
        )
        student_count = student_count_result.scalar() or 0

        # Calculate class avg_mastery from all enrolled students' topic progress
        enrolled = await db.execute(
            select(ClassEnrollment.student_id).where(ClassEnrollment.class_id == c.id)
        )
        student_ids = [r[0] for r in enrolled.fetchall()]

        avg_mastery = 0.0
        if student_ids:
            mastery_result = await db.execute(
                select(func.avg(StudentTopicProgress.mastery_score))
                .where(StudentTopicProgress.student_id.in_(student_ids))
            )
            raw_avg = mastery_result.scalar()
            avg_mastery = round(raw_avg, 1) if raw_avg else 0.0

        responses.append(ClassResponse(
            id=c.id,
            name=c.name,
            teacher_id=c.teacher_id,
            subject=c.subject,
            invite_code=c.invite_code,
            created_at=c.created_at,
            student_count=student_count,
            avg_mastery=avg_mastery,
        ))
    return responses


@router.get("/classes/{class_id}", response_model=ClassDetailResponse)
async def get_class_detail(
    class_id: int,
    user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db),
):
    """Returns class detail including student count and assignment count."""
    if user.role not in ["teacher", "admin"]:
        raise HTTPException(status_code=403, detail="Teacher only")
    teacher = await _get_teacher(db, user.id)

    class_result = await db.execute(
        select(Class).where(Class.id == class_id, Class.teacher_id == teacher.id)
    )
    class_ = class_result.scalar_one_or_none()
    if not class_:
        raise HTTPException(status_code=404, detail="Class not found")

    # Count enrolled students
    student_count_result = await db.execute(
        select(func.count(ClassEnrollment.id)).where(ClassEnrollment.class_id == class_id)
    )
    student_count = student_count_result.scalar() or 0

    # Count assignments
    assignment_count_result = await db.execute(
        select(func.count(Assignment.id)).where(Assignment.class_id == class_id)
    )
    assignment_count = assignment_count_result.scalar() or 0

    return ClassDetailResponse(
        id=class_.id,
        name=class_.name,
        teacher_id=class_.teacher_id,
        subject=class_.subject,
        invite_code=class_.invite_code,
        created_at=class_.created_at,
        student_count=student_count,
        assignment_count=assignment_count,
    )


@router.get("/classes/{class_id}/students", response_model=list[ClassStudentsResponse])
async def get_class_students(
    class_id: int,
    user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db),
):
    if user.role not in ["teacher", "admin"]:
        raise HTTPException(status_code=403, detail="Teacher only")
    teacher = await _get_teacher(db, user.id)

    class_result = await db.execute(
        select(Class).where(Class.id == class_id, Class.teacher_id == teacher.id)
    )
    class_ = class_result.scalar_one_or_none()
    if not class_:
        raise HTTPException(status_code=404, detail="Class not found")

    result = await db.execute(
        select(ClassEnrollment)
        .where(ClassEnrollment.class_id == class_id)
        .options(selectinload(ClassEnrollment.student).selectinload(Student.user))
    )

    students_data = []
    for enrollment in result.scalars().all():
        student = enrollment.student

        # Calculate real avg_mastery from StudentTopicProgress
        mastery_result = await db.execute(
            select(func.avg(StudentTopicProgress.mastery_score)).where(
                StudentTopicProgress.student_id == student.id
            )
        )
        avg_mastery = mastery_result.scalar() or 0.0

        # last_active: use Student.last_activity_date, fall back to most recent attempt
        last_active = student.last_activity_date
        if not last_active:
            recent = await db.execute(
                select(func.max(ExerciseAttempt.attempted_at))
                .where(ExerciseAttempt.student_id == student.id)
            )
            last_active = recent.scalar()

        # exercises_completed: sum from StudentTopicProgress
        ex_completed_result = await db.execute(
            select(func.sum(StudentTopicProgress.exercises_completed))
            .where(StudentTopicProgress.student_id == student.id)
        )
        exercises_completed = ex_completed_result.scalar() or 0

        students_data.append(
            ClassStudentsResponse(
                student_id=student.id,
                name=student.user.name,
                email=student.user.email,
                grade=student.grade,
                points=student.points,
                level=student.level,
                current_streak=student.current_streak,
                avg_mastery=avg_mastery,
                enrolled_at=enrollment.enrolled_at,
                last_active=last_active,
                exercises_completed=exercises_completed,
            )
        )
    return students_data


@router.get("/classes/{class_id}/assignments", response_model=list[AssignmentResponse])
async def get_class_assignments(
    class_id: int,
    user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db),
):
    """List all assignments for a class."""
    if user.role not in ["teacher", "admin"]:
        raise HTTPException(status_code=403, detail="Teacher only")
    teacher = await _get_teacher(db, user.id)

    class_result = await db.execute(
        select(Class).where(Class.id == class_id, Class.teacher_id == teacher.id)
    )
    class_ = class_result.scalar_one_or_none()
    if not class_:
        raise HTTPException(status_code=404, detail="Class not found")

    result = await db.execute(
        select(Assignment)
        .where(Assignment.class_id == class_id)
        .order_by(Assignment.created_at.desc())
    )
    return [AssignmentResponse.model_validate(a) for a in result.scalars().all()]


@router.post("/classes/{class_id}/assignments", response_model=AssignmentResponse)
async def create_class_assignment(
    class_id: int,
    data: AssignmentCreateRequest,
    user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db),
):
    """Create an assignment scoped to a specific class (teacher-owned)."""
    if user.role not in ["teacher", "admin"]:
        raise HTTPException(status_code=403, detail="Teacher only")
    teacher = await _get_teacher(db, user.id)

    class_result = await db.execute(
        select(Class).where(Class.id == class_id, Class.teacher_id == teacher.id)
    )
    class_ = class_result.scalar_one_or_none()
    if not class_:
        raise HTTPException(status_code=404, detail="Class not found")

    assignment = Assignment(
        class_id=class_id,
        title=data.title,
        description=data.description,
        due_date=data.due_date,
    )
    db.add(assignment)
    await db.flush()
    for i, exercise_id in enumerate(data.exercise_ids):
        ae = AssignmentExercise(assignment_id=assignment.id, exercise_id=exercise_id, order_index=i)
        db.add(ae)
    await db.commit()
    await db.refresh(assignment)
    return AssignmentResponse.model_validate(assignment)


async def _get_teacher(db: AsyncSession, user_id: int) -> Teacher:
    result = await db.execute(select(Teacher).where(Teacher.user_id == user_id))
    teacher = result.scalar_one_or_none()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher profile not found")
    return teacher


@router.delete("/classes/{class_id}/students/{student_id}")
async def remove_student_from_class(
    class_id: int,
    student_id: int,
    user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db),
):
    """Remove a student from a class."""
    if user.role not in ["teacher", "admin"]:
        raise HTTPException(status_code=403, detail="Teacher only")
    teacher = await _get_teacher(db, user.id)

    # Verify teacher owns the class
    result = await db.execute(select(Class).where(Class.id == class_id, Class.teacher_id == teacher.id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Class not found")

    # Remove enrollment
    enrollment_result = await db.execute(
        select(ClassEnrollment)
        .where(ClassEnrollment.class_id == class_id, ClassEnrollment.student_id == student_id)
    )
    enrollment = enrollment_result.scalar_one_or_none()
    if not enrollment:
        raise HTTPException(status_code=404, detail="Student not enrolled")

    await db.delete(enrollment)
    await db.commit()
    return {"message": "Student removed"}


@router.delete("/classes/{class_id}/assignments/{assignment_id}")
async def delete_assignment(
    class_id: int,
    assignment_id: int,
    user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db),
):
    """Delete an assignment and its exercise associations."""
    if user.role not in ["teacher", "admin"]:
        raise HTTPException(status_code=403, detail="Teacher only")
    teacher = await _get_teacher(db, user.id)

    # Verify teacher owns the class
    result = await db.execute(select(Class).where(Class.id == class_id, Class.teacher_id == teacher.id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Class not found")

    # Delete assignment exercises first
    await db.execute(
        delete(AssignmentExercise).where(AssignmentExercise.assignment_id == assignment_id)
    )
    # Delete student assignment records
    await db.execute(
        delete(StudentAssignment).where(StudentAssignment.assignment_id == assignment_id)
    )
    # Delete the assignment
    await db.execute(delete(Assignment).where(Assignment.id == assignment_id))
    await db.commit()
    return {"message": "Assignment deleted"}
