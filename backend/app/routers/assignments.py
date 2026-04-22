from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import get_current_user_required
from app.models.user import User, Student
from app.models.classes import Assignment, AssignmentExercise, StudentAssignment, Class, ClassEnrollment
from app.models.progress import ExerciseAttempt
from app.models.notification import Notification
from app.models.curriculum import Exercise
from app.schemas.assignment import (
    AssignmentCreateRequest, AssignmentResponse,
    AssignmentResultResponse, StudentAssignmentResult, ExerciseResultItem,
)

router = APIRouter()


@router.post("", response_model=AssignmentResponse)
async def create_assignment(
    data: AssignmentCreateRequest,
    user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db),
):
    if user.role not in ["teacher", "admin"]:
        raise HTTPException(status_code=403, detail="Teacher only")
    assignment = Assignment(
        class_id=data.class_id,
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

    # Create notifications for all enrolled students
    enrolled = await db.execute(
        select(ClassEnrollment)
        .where(ClassEnrollment.class_id == assignment.class_id)
        .options(selectinload(ClassEnrollment.student).selectinload(Student.user))
    )
    for enrollment in enrolled.scalars().all():
        notification = Notification(
            user_id=enrollment.student.user_id,
            type="new_assignment",
            title=f"Nueva tarea: {assignment.title}",
            body=f"Se ha asignado una nueva tarea en tu clase.",
            link=f"/me/assignments/{assignment.id}"
        )
        db.add(notification)
    await db.commit()

    return AssignmentResponse.model_validate(assignment)


@router.get("/{assignment_id}/results", response_model=AssignmentResultResponse)
async def get_assignment_results(
    assignment_id: int,
    user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns detailed results for an assignment:
    - Per student: score, completion rate, per-exercise breakdown
    - Class-level: average score, completion rate
    """
    if user.role not in ["teacher", "admin"]:
        raise HTTPException(status_code=403, detail="Teacher only")

    # Load assignment
    ass_result = await db.execute(
        select(Assignment).where(Assignment.id == assignment_id)
    )
    assignment = ass_result.scalar_one_or_none()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    # Load the exercises in this assignment (ordered)
    ae_result = await db.execute(
        select(AssignmentExercise)
        .where(AssignmentExercise.assignment_id == assignment_id)
        .order_by(AssignmentExercise.order_index)
    )
    assignment_exercises = ae_result.scalars().all()
    exercise_ids = [ae.exercise_id for ae in assignment_exercises]
    total_exercises = len(exercise_ids)

    if total_exercises == 0:
        return AssignmentResultResponse(
            assignment_id=assignment_id,
            title=assignment.title,
            total_students=0,
            completed_count=0,
            avg_score=None,
            completion_rate=0.0,
            results=[],
        )

    # Load all student assignments for this class
    sa_result = await db.execute(
        select(StudentAssignment)
        .where(StudentAssignment.assignment_id == assignment_id)
    )
    student_assignments = sa_result.scalars().all()

    student_results: list[StudentAssignmentResult] = []
    total_scores: list[float] = []
    completed_count = 0

    for sa in student_assignments:
        # Load the student user info
        student_result = await db.execute(
            select(Student).where(Student.id == sa.student_id).options(selectinload(Student.user))
        )
        student = student_result.scalar_one_or_none()
        if not student:
            continue

        # Get all attempt rows for this student + this assignment's exercises
        attempts_result = await db.execute(
            select(ExerciseAttempt)
            .where(
                ExerciseAttempt.student_id == sa.student_id,
                ExerciseAttempt.exercise_id.in_(exercise_ids),
            )
            .order_by(ExerciseAttempt.attempted_at)
        )
        all_attempts = attempts_result.scalars().all()

        # Per-exercise results: best attempt per exercise (most recent correct if multiple)
        # Build a map: exercise_id -> best attempt (correct if any, else first attempt)
        best_attempts: dict[int, ExerciseAttempt] = {}
        for att in all_attempts:
            eid = att.exercise_id
            if eid not in best_attempts or (att.correct and not best_attempts[eid].correct):
                best_attempts[eid] = att

        exercise_results: list[ExerciseResultItem] = []
        correct_count = 0
        for ae in assignment_exercises:
            att = best_attempts.get(ae.exercise_id)
            if att:
                correct_flag = att.correct
                if correct_flag:
                    correct_count += 1
                ex_result = await db.execute(
                    select(Exercise).where(Exercise.id == ae.exercise_id)
                )
                exercise = ex_result.scalar_one_or_none()
                exercise_results.append(ExerciseResultItem(
                    exercise_id=ae.exercise_id,
                    exercise_title=exercise.title if exercise else f"Ejercicio {ae.exercise_id}",
                    correct=correct_flag,
                    points_earned=att.points_earned,
                    xp_earned=att.xp_earned,
                ))
            else:
                # No attempt for this exercise
                ex_result = await db.execute(
                    select(Exercise).where(Exercise.id == ae.exercise_id)
                )
                exercise = ex_result.scalar_one_or_none()
                exercise_results.append(ExerciseResultItem(
                    exercise_id=ae.exercise_id,
                    exercise_title=exercise.title if exercise else f"Ejercicio {ae.exercise_id}",
                    correct=False,
                    points_earned=0,
                    xp_earned=0,
                ))

        completion_rate = len(best_attempts) / total_exercises if total_exercises > 0 else 0.0
        score = (correct_count / total_exercises * 100) if total_exercises > 0 else 0.0

        if sa.completed_at:
            completed_count += 1
            total_scores.append(score)

        student_results.append(StudentAssignmentResult(
            student_id=sa.student_id,
            student_name=student.user.name,
            score=round(score, 1),
            completion_rate=round(completion_rate * 100, 1),
            completed_at=sa.completed_at,
            started_at=sa.started_at,
            exercises=exercise_results,
        ))

    total_students = len(student_assignments)
    avg_score = round(sum(total_scores) / len(total_scores), 1) if total_scores else None
    completion_rate_pct = round(completed_count / total_students * 100, 1) if total_students > 0 else 0.0

    return AssignmentResultResponse(
        assignment_id=assignment_id,
        title=assignment.title,
        total_students=total_students,
        completed_count=completed_count,
        avg_score=avg_score,
        completion_rate=completion_rate_pct,
        results=student_results,
    )
