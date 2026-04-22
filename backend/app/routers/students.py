from datetime import date, timedelta, datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_current_user_required
from app.core.redis import get_redis
from app.models.user import User, Student, Teacher, UserRole
from app.models.parent import Parent, ParentStudentLink
from app.models.progress import ExerciseAttempt, StudentTopicProgress
from app.models.gamification import Achievement
from app.models.notification import Notification
from app.models.curriculum import Exercise, Unit, Lesson, Topic
from app.models.classes import Assignment, AssignmentExercise, Class, ClassEnrollment, StudentAssignment
from app.schemas.student import (
    ProgressResponse, AttemptRequest, AttemptResponse,
    AchievementResponse, StreakResponse, StatsResponse, StreakFreezeResponse,
    AttemptHistoryResponse, AttemptHistoryItem, MyClassItem,
)
from app.schemas.assignment import (
    MyAssignmentsResponse, StudentAssignmentDetail,
    StudentAssignmentListItem, ExerciseInAssignment,
)

router = APIRouter()

# XP constants
XP_CORRECT = 10
XP_FIRST_TRY_BONUS = 5
XP_STREAK_BONUS_PER_DAY = 2
XP_LESSON_COMPLETE = 20

@router.get("/progress", response_model=list[ProgressResponse])
async def get_my_progress(user: User = Depends(get_current_user_required), db: AsyncSession = Depends(get_db)):
    if user.role != "student":
        raise HTTPException(status_code=403, detail="Student only")
    student = await _get_student(db, user.id)

    # Get all root topics (parent_id = None) for the seed topics
    topics_result = await db.execute(select(Topic).where(Topic.parent_id == None))
    all_topics = {t.id: t for t in topics_result.scalars().all()}

    result = await db.execute(
        select(StudentTopicProgress).where(StudentTopicProgress.student_id == student.id)
    )
    progress_rows = result.scalars().all()

    # If no progress rows yet, create them for each topic with 0 mastery
    if not progress_rows:
        progress_list = []
        for topic_id, topic in all_topics.items():
            # Count total exercises in this topic
            total_ex_result = await db.execute(
                select(func.count(Exercise.id))
                .join(Unit, Unit.id == Exercise.unit_id)
                .where(Unit.topic_id == topic_id)
            )
            total_ex = total_ex_result.scalar() or 0

            new_progress = StudentTopicProgress(
                student_id=student.id,
                topic_id=topic_id,
                exercises_completed=0,
                total_exercises=total_ex,
                mastery_score=0.0,
            )
            db.add(new_progress)
            progress_list.append(new_progress)

        if all_topics:
            await db.commit()
            for p in progress_list:
                await db.refresh(p)
        else:
            return []

        progress_rows = progress_list

    # Recalculate total_exercises dynamically from DB
    enriched = []
    for p in progress_rows:
        total_ex_result = await db.execute(
            select(func.count(Exercise.id))
            .join(Unit, Unit.id == Exercise.unit_id)
            .where(Unit.topic_id == p.topic_id)
        )
        current_total = total_ex_result.scalar() or 0
        enriched.append((p, current_total))

    return [
        ProgressResponse(
            topic_id=p.topic_id,
            topic_title=all_topics.get(p.topic_id, type('T', (object,), {'title': f'Topic {p.topic_id}'})()).title,
            exercises_completed=p.exercises_completed,
            total_exercises=current_total,
            mastery_score=p.mastery_score,
        )
        for p, current_total in enriched
        if p.topic_id in all_topics
    ]


@router.post("/streaks/freeze", response_model=StreakFreezeResponse)
async def use_streak_freeze(user: User = Depends(get_current_user_required), db: AsyncSession = Depends(get_db)):
    """
    Use one streak freeze to protect the current streak.
    The freeze prevents the streak from resetting for today's gap.
    """
    if user.role != "student":
        raise HTTPException(status_code=403, detail="Student only")
    student = await _get_student(db, user.id)

    if student.streak_freeze_available <= 0:
        return StreakFreezeResponse(
            success=False,
            message="No tienes hielos de racha disponibles",
            freezes_remaining=0,
        )

    # Consume one freeze
    student.streak_freeze_available -= 1
    student.streak_freeze_used_count += 1
    student.streak_frozen = True  # protection flag for today's check
    await db.commit()

    # Check for first_freeze achievement
    new_achievements = await _check_achievements(db, student)

    from app.schemas.student import AchievementResponse
    return StreakFreezeResponse(
        success=True,
        message="¡Racha protegida con hielo! 🎉",
        freezes_remaining=student.streak_freeze_available,
        new_achievements=[AchievementResponse.model_validate(a) for a in new_achievements],
    )
@router.post("/exercises/{exercise_id}/attempt", response_model=AttemptResponse)
async def submit_attempt(exercise_id: int, data: AttemptRequest, user: User = Depends(get_current_user_required), db: AsyncSession = Depends(get_db)):
    if user.role != "student":
        raise HTTPException(status_code=403, detail="Student only")
    student = await _get_student(db, user.id)
    result = await db.execute(select(Exercise).where(Exercise.id == exercise_id))
    exercise = result.scalar_one_or_none()
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")

    correct_answer = exercise.data.get("correct_answer")
    choices = exercise.data.get("choices")

    correct = False
    et = exercise.exercise_type.value if hasattr(exercise.exercise_type, 'value') else str(exercise.exercise_type)
    if et == "multiple_choice" and choices:
        correct = str(data.answer).strip().lower() == str(correct_answer).strip().lower()
    elif et == "true_false":
        correct = str(data.answer).strip().lower() == str(correct_answer).strip().lower()
    else:
        correct = str(data.answer).strip().lower() == str(correct_answer).strip().lower() if correct_answer else False

    # Calculate XP
    xp_earned = XP_CORRECT if correct else 0

    # First-try bonus: check if this is the student's first attempt at this exercise
    first_attempt_result = await db.execute(
        select(ExerciseAttempt)
        .where(ExerciseAttempt.student_id == student.id, ExerciseAttempt.exercise_id == exercise_id)
        .order_by(ExerciseAttempt.id)
    )
    first_attempt = first_attempt_result.scalars().first()
    if correct and first_attempt is None:
        xp_earned += XP_FIRST_TRY_BONUS  # First-try bonus

    points_earned = exercise.points_value if correct else 0

    attempt = ExerciseAttempt(
        student_id=student.id,
        exercise_id=exercise_id,
        assignment_id=data.assignment_id,
        answer_json={"answer": data.answer},
        correct=correct,
        points_earned=points_earned,
        xp_earned=xp_earned,
        time_spent_seconds=data.time_spent_seconds
    )
    db.add(attempt)

    today = date.today()
    streak_updated = False

    if correct:
        student.points += points_earned
        student.total_xp += xp_earned
        student.level = (student.total_xp // 100) + 1

        # Update streak
        if student.last_activity_date is None:
            student.current_streak = 1
            student.longest_streak = max(student.longest_streak, 1)
            streak_updated = True
        elif student.last_activity_date == today:
            # Already checked in today, no change
            streak_updated = False
        elif student.last_activity_date == today - timedelta(days=1):
            # Consecutive day — increment
            student.current_streak += 1
            student.longest_streak = max(student.longest_streak, student.current_streak)
            student.total_xp += XP_STREAK_BONUS_PER_DAY  # streak bonus
            xp_earned += XP_STREAK_BONUS_PER_DAY
            streak_updated = True
        else:
            # Gap — reset streak
            student.current_streak = 1
            streak_updated = True

        student.last_activity_date = today

        redis = await get_redis()
        await redis.zincrby("leaderboard:global:all_time", points_earned, student.id)
        await redis.zincrby("leaderboard:global:weekly", points_earned, student.id)

    await db.commit()

    # ── Assignment Completion Check ──────────────────────────────────────────
    if data.assignment_id is not None:
        # Get all exercise IDs for this assignment
        assignment_exs = await db.execute(
            select(AssignmentExercise.exercise_id).where(AssignmentExercise.assignment_id == data.assignment_id)
        )
        exercise_ids = [r for (r,) in assignment_exs.all()]

        # Count how many of those exercises this student has correct attempts for
        if exercise_ids:
            correct_count = await db.execute(
                select(func.count(func.distinct(ExerciseAttempt.exercise_id)))
                .where(ExerciseAttempt.student_id == student.id)
                .where(ExerciseAttempt.exercise_id.in_(exercise_ids))
                .where(ExerciseAttempt.correct == True)
            )
            correct_total = correct_count.scalar() or 0

            # If all exercises have at least one correct attempt, mark assignment complete
            if correct_total >= len(exercise_ids):
                sa_query = select(StudentAssignment).where(
                    StudentAssignment.student_id == student.id,
                    StudentAssignment.assignment_id == data.assignment_id
                )
                sa_result = await db.execute(sa_query)
                sa = sa_result.scalar_one_or_none()
                if sa and sa.completed_at is None:
                    sa.completed_at = datetime.now(timezone.utc)
                    # Compute score: % of exercises with at least one correct attempt
                    score_result = await db.execute(
                        select(func.count(func.distinct(ExerciseAttempt.exercise_id)))
                        .where(ExerciseAttempt.student_id == student.id)
                        .where(ExerciseAttempt.exercise_id.in_(exercise_ids))
                        .where(ExerciseAttempt.correct == True)
                    )
                    correct_count_val = score_result.scalar() or 0
                    sa.score = round(correct_count_val / len(exercise_ids) * 100, 1) if exercise_ids else 0.0
                    await db.commit()

                    # Notify teacher that student completed the assignment
                    assignment_result = await db.execute(select(Assignment).where(Assignment.id == data.assignment_id))
                    assignment = assignment_result.scalar_one_or_none()
                    if assignment:
                        class_result = await db.execute(select(Class).where(Class.id == assignment.class_id))
                        class_obj = class_result.scalar_one_or_none()
                        if class_obj:
                            teacher_result = await db.execute(select(Teacher).where(Teacher.id == class_obj.teacher_id))
                            teacher = teacher_result.scalar_one_or_none()
                            if teacher:
                                notification = Notification(
                                    user_id=teacher.user_id,
                                    type="assignment_completed",
                                    title=f"📝 {student.user.name} completó la tarea: {assignment.title}",
                                    body=f"Ve los resultados en la página de la tarea.",
                                    link=f"/teacher/classes/{assignment.class_id}/assignments/{assignment.id}/results"
                                )
                                db.add(notification)
                                await db.commit()

    # ── Mastery Calculation ───────────────────────────────────────────────
    # Get the topic for this exercise
    unit_result = await db.execute(select(Unit).where(Unit.id == exercise.unit_id))
    unit = unit_result.scalar_one_or_none()
    topic_id = unit.topic_id if unit else None
    new_mastery = 0.0

    if correct and topic_id is not None:
        topic_id_int = int(topic_id)

        # Upsert StudentTopicProgress
        prog_result = await db.execute(
            select(StudentTopicProgress).where(
                StudentTopicProgress.student_id == student.id,
                StudentTopicProgress.topic_id == topic_id_int,
            )
        )
        progress_row = prog_result.scalar_one_or_none()

        # Count total unique exercises in this topic
        total_ex_result = await db.execute(
            select(func.count(Exercise.id))
            .join(Unit, Unit.id == Exercise.unit_id)
            .where(Unit.topic_id == topic_id_int)
        )
        total_exercises = total_ex_result.scalar() or 0

        if progress_row is None:
            progress_row = StudentTopicProgress(
                student_id=student.id,
                topic_id=topic_id_int,
                exercises_completed=0,
                total_exercises=total_exercises,
                mastery_score=0.0,
            )
            db.add(progress_row)
            await db.flush()

        # Increment exercises completed (only count first-time correct attempts)
        existing_correct = await db.execute(
            select(ExerciseAttempt.id)
            .where(ExerciseAttempt.student_id == student.id)
            .where(ExerciseAttempt.exercise_id == exercise_id)
            .where(ExerciseAttempt.correct == True)
            .limit(1)
        )
        if existing_correct.scalar_one_or_none() is None:
            # This is the first correct attempt for this exercise
            progress_row.exercises_completed = progress_row.exercises_completed + 1

        # Recalculate mastery: weighted average
        # Recent attempts (last 5) count double; older count once
        recent_result = await db.execute(
            select(ExerciseAttempt)
            .join(Exercise, Exercise.id == ExerciseAttempt.exercise_id)
            .join(Unit, Unit.id == Exercise.unit_id)
            .where(
                ExerciseAttempt.student_id == student.id,
                ExerciseAttempt.correct == True,
                Unit.topic_id == topic_id_int,
            )
            .order_by(ExerciseAttempt.id.desc())
            .limit(10)
        )
        recent_correct = recent_result.scalars().all()
        n = len(recent_correct)
        if n == 0:
            weighted_score = 0.0
        else:
            # Last 5 correct: weight=2, older: weight=1
            recent_five = recent_correct[:5]
            older = recent_correct[5:]
            weighted_score = (len(recent_five) * 2 + len(older) * 1) / (n * 2) * 100

        progress_row.mastery_score = round(weighted_score, 2)
        new_mastery = progress_row.mastery_score

        # Update total_exercises if not set yet
        if progress_row.total_exercises == 0 and total_exercises > 0:
            progress_row.total_exercises = total_exercises

        await db.commit()

    # Check and award achievements — get back the newly earned ones
    new_achievements = await _check_achievements(db, student)

    return AttemptResponse(
        correct=correct,
        points_earned=points_earned,
        xp_earned=xp_earned,
        explanation=exercise.data.get("explanation"),
        new_mastery=new_mastery,
        streak_updated=streak_updated,
        current_streak=student.current_streak,
        new_achievements=[AchievementResponse.model_validate(a) for a in new_achievements],
    )


@router.get("/streaks/me", response_model=StreakResponse)
async def get_my_streak(user: User = Depends(get_current_user_required), db: AsyncSession = Depends(get_db)):
    """Get current user's streak info."""
    if user.role != "student":
        raise HTTPException(status_code=403, detail="Student only")
    student = await _get_student(db, user.id)
    today = date.today()
    streak_at_risk = False
    if student.last_activity_date is not None:
        diff = (today - student.last_activity_date).days
        streak_at_risk = diff == 1  # at risk if last activity was yesterday (hasn't checked in today)
    return StreakResponse(
        current_streak=student.current_streak,
        longest_streak=student.longest_streak,
        last_activity_date=student.last_activity_date,
        streak_freeze_available=student.streak_freeze_available,
        streak_at_risk=streak_at_risk
    )


@router.get("/stats/me", response_model=StatsResponse)
async def get_my_stats(user: User = Depends(get_current_user_required), db: AsyncSession = Depends(get_db)):
    """Get current user's XP and progress stats."""
    if user.role != "student":
        raise HTTPException(status_code=403, detail="Student only")
    student = await _get_student(db, user.id)

    # Count exercises completed
    attempts_result = await db.execute(
        select(ExerciseAttempt).where(ExerciseAttempt.student_id == student.id, ExerciseAttempt.correct == True)
    )
    exercises_completed = len(set(a.exercise_id for a in attempts_result.scalars().all()))

    # Count lessons completed (unique lessons with at least 1 correct attempt)
    lesson_result = await db.execute(
        select(Exercise.lesson_id)
        .join(ExerciseAttempt, ExerciseAttempt.exercise_id == Exercise.id)
        .where(ExerciseAttempt.student_id == student.id, ExerciseAttempt.correct == True, Exercise.lesson_id != None)
    )
    lessons_completed = len(set(r[0] for r in lesson_result.fetchall() if r[0] is not None))

    xp_for_level = student.total_xp % 100
    xp_to_next_level = 100 - xp_for_level

    return StatsResponse(
        total_xp=student.total_xp,
        level=student.level,
        points=student.points,
        current_streak=student.current_streak,
        longest_streak=student.longest_streak,
        exercises_completed=exercises_completed,
        lessons_completed=lessons_completed,
        xp_to_next_level=xp_to_next_level
    )


ACHIEVEMENT_DEFINITIONS = [
    {"slug": "primer-paso", "name": "Primer Paso", "description": "Completa tu primer ejercicio", "icon": "🎯", "trigger": "first_exercise"},
    {"slug": "racha-3", "name": "Racha de 3", "description": "3 días de racha consecutivos", "icon": "🔥", "trigger": "streak_3"},
    {"slug": "racha-7", "name": "Semana Perfecta", "description": "7 días de racha consecutivos", "icon": "🔥", "trigger": "streak_7"},
    {"slug": "racha-14", "name": "Quincena", "description": "14 días de racha consecutivos", "icon": "🔥", "trigger": "streak_14"},
    {"slug": "racha-30", "name": "Rey de la Racha", "description": "30 días de racha consecutivos", "icon": "🔥", "trigger": "streak_30"},
    {"slug": "mateador", "name": "Mateador", "description": "Gana 100 puntos totales", "icon": "⭐", "trigger": "points_100"},
    {"slug": "experto", "name": "Experto", "description": "Gana 500 puntos totales", "icon": "🏆", "trigger": "points_500"},
    {"slug": "maestro", "name": "Maestro", "description": "Gana 1000 puntos totales", "icon": "👑", "trigger": "points_1000"},
    {"slug": "primera-clase", "name": "Primera Clase", "description": "Completa tu primera lección", "icon": "📚", "trigger": "first_lesson"},
    {"slug": "inmune", "name": "Inmune", "description": "Usa tu primer hielo de racha", "icon": "🧊", "trigger": "first_freeze"},
    {"slug": "racha-imparable", "name": "Racha Imparable", "description": "8 ejercicios correctos seguidos en una sesión", "icon": "💪", "trigger": "session_8"},
]


async def _check_achievements(db: AsyncSession, student: Student) -> list[Achievement]:
    """
    Check and award achievements based on student progress.
    Returns the list of *newly* earned Achievement rows.
    """
    try:
        existing = await db.execute(select(Achievement).where(Achievement.student_id == student.id))
        existing_achievements = existing.scalars().all()
        existing_slugs = {a.badge_key for a in existing_achievements}

        total_attempts_result = await db.execute(select(ExerciseAttempt).where(ExerciseAttempt.student_id == student.id))
        total_attempts = len(total_attempts_result.scalars().all())

        # Session streak: consecutive correct attempts in a row (for session_X triggers)
        session_streak_result = await db.execute(
            select(ExerciseAttempt)
            .where(ExerciseAttempt.student_id == student.id)
            .order_by(ExerciseAttempt.id.desc())
        )
        session_streak = 0
        for attempt in session_streak_result.scalars().all():
            if attempt.correct:
                session_streak += 1
            else:
                break

        achievements_to_add = []
        for defn in ACHIEVEMENT_DEFINITIONS:
            if defn["slug"] in existing_slugs:
                continue
            trigger = defn["trigger"]
            award = False
            if trigger == "first_exercise" and total_attempts >= 1:
                award = True
            elif trigger == "streak_3" and student.current_streak >= 3:
                award = True
            elif trigger == "streak_7" and student.current_streak >= 7:
                award = True
            elif trigger == "streak_14" and student.current_streak >= 14:
                award = True
            elif trigger == "streak_30" and student.current_streak >= 30:
                award = True
            elif trigger == "points_100" and student.points >= 100:
                award = True
            elif trigger == "points_500" and student.points >= 500:
                award = True
            elif trigger == "points_1000" and student.points >= 1000:
                award = True
            elif trigger == "first_lesson":
                # Check unique lessons completed
                lesson_result = await db.execute(
                    select(Exercise.lesson_id)
                    .join(ExerciseAttempt, ExerciseAttempt.exercise_id == Exercise.id)
                    .where(ExerciseAttempt.student_id == student.id, ExerciseAttempt.correct == True, Exercise.lesson_id != None)
                )
                unique_lessons = len(set(r for r in lesson_result.fetchall() if r[0] is not None))
                award = unique_lessons >= 1
            elif trigger == "first_freeze" and student.streak_freeze_used_count > 0:
                award = True
            elif trigger == "session_8" and session_streak >= 8:
                award = True
            if award:
                achievements_to_add.append(defn)

        new_achievements = []
        for defn in achievements_to_add:
            achievement = Achievement(
                student_id=student.id,
                badge_key=defn["slug"],
                title=defn["name"],
                description=defn["description"],
                icon=defn["icon"]
            )
            db.add(achievement)
            new_achievements.append(achievement)

        if achievements_to_add:
            await db.commit()
            for a in new_achievements:
                await db.refresh(a)
                notification = Notification(
                    user_id=student.user_id,
                    type="achievement",
                    title=f"🏆 ¡Logro desbloqueado!",
                    body=f"Has obtenido: {a.title} — {a.description}",
                    link=f"/me/achievements"
                )
                db.add(notification)
            await db.commit()

        return new_achievements
    except Exception as e:
        print(f"[_check_achievements] Error: {e}")
        return []

@router.get("/achievements", response_model=list[AchievementResponse])
async def get_my_achievements(user: User = Depends(get_current_user_required), db: AsyncSession = Depends(get_db)):
    if user.role != "student":
        raise HTTPException(status_code=403, detail="Student only")
    student = await _get_student(db, user.id)
    result = await db.execute(select(Achievement).where(Achievement.student_id == student.id))
    return [AchievementResponse.model_validate(a) for a in result.scalars().all()]


@router.get("/history", response_model=AttemptHistoryResponse)
async def get_my_attempt_history(
    user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db),
    topic_id: int | None = Query(None, description="Filter by topic ID"),
    unit_id: int | None = Query(None, description="Filter by unit ID"),
    correct: bool | None = Query(None, description="Filter by correct (true/false)"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    """
    Paginated attempt history for the current student.
    Supports filtering by topic, unit, and correctness.
    """
    if user.role != "student":
        raise HTTPException(status_code=403, detail="Student only")
    student = await _get_student(db, user.id)

    # Build base query
    base_query = (
        select(ExerciseAttempt, Exercise, Unit, Topic)
        .join(Exercise, Exercise.id == ExerciseAttempt.exercise_id)
        .join(Unit, Unit.id == Exercise.unit_id)
        .join(Topic, Topic.id == Unit.topic_id)
        .where(ExerciseAttempt.student_id == student.id)
    )

    if topic_id is not None:
        base_query = base_query.where(Unit.topic_id == topic_id)
    if unit_id is not None:
        base_query = base_query.where(Unit.id == unit_id)
    if correct is not None:
        base_query = base_query.where(ExerciseAttempt.correct == correct)

    # Total count
    count_q = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_q)
    total = total_result.scalar() or 0

    # Paginated results
    offset = (page - 1) * limit
    paged_query = (
        base_query
        .order_by(desc(ExerciseAttempt.attempted_at))
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(paged_query)
    rows = result.all()

    items = [
        AttemptHistoryItem(
            id=attempt.id,
            exercise_id=attempt.exercise_id,
            exercise_title=exercise.title,
            topic_title=topic.title,
            topic_id=topic.id,
            unit_title=unit.title,
            unit_id=unit.id,
            correct=attempt.correct,
            answer=(attempt.answer_json or {}).get("answer"),
            correct_answer=exercise.data.get("correct_answer"),
            xp_earned=attempt.xp_earned,
            points_earned=attempt.points_earned,
            attempted_at=attempt.attempted_at,
        )
        for attempt, exercise, unit, topic in rows
    ]

    pages = (total + limit - 1) // limit if limit > 0 else 0

    return AttemptHistoryResponse(
        items=items,
        total=total,
        page=page,
        pages=pages,
        limit=limit,
    )


@router.get("/assignments", response_model=MyAssignmentsResponse)
async def get_my_assignments(
    user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db),
):
    """Get all assignments for the current student."""
    student = await _get_student(db, user.id)

    enrolled = await db.execute(
        select(ClassEnrollment.class_id).where(ClassEnrollment.student_id == student.id)
    )
    class_ids = [r for (r,) in enrolled.all()]

    if not class_ids:
        return MyAssignmentsResponse(items=[], total=0)

    assignments_result = await db.execute(
        select(Assignment, Class.name)
        .join(Class, Assignment.class_id == Class.id)
        .where(Assignment.class_id.in_(class_ids))
        .order_by(Assignment.due_date.asc().nullslast())
    )

    items = []
    for (assignment, class_name) in assignments_result.all():
        sa_result = await db.execute(
            select(StudentAssignment).where(
                StudentAssignment.student_id == student.id,
                StudentAssignment.assignment_id == assignment.id
            )
        )
        sa = sa_result.scalar_one_or_none()

        ex_result = await db.execute(
            select(AssignmentExercise.exercise_id).where(AssignmentExercise.assignment_id == assignment.id)
        )
        exercise_ids = [r for (r,) in ex_result.all()]
        total_exercises = len(exercise_ids)

        if total_exercises > 0:
            correct_result = await db.execute(
                select(func.count(func.distinct(ExerciseAttempt.exercise_id)))
                .where(ExerciseAttempt.student_id == student.id)
                .where(ExerciseAttempt.exercise_id.in_(exercise_ids))
                .where(ExerciseAttempt.correct == True)
            )
            correct_count = correct_result.scalar() or 0
            completion_rate = correct_count / total_exercises
        else:
            completion_rate = 0.0

        items.append(StudentAssignmentListItem(
            id=assignment.id,
            title=assignment.title,
            description=assignment.description,
            due_date=assignment.due_date,
            class_id=assignment.class_id,
            class_name=class_name,
            score=sa.score if sa else None,
            completion_rate=round(completion_rate, 4),
            completed_at=sa.completed_at if sa else None,
        ))

    return MyAssignmentsResponse(items=items, total=len(items))


@router.get("/assignments/{assignment_id}", response_model=StudentAssignmentDetail)
async def get_my_assignment_detail(
    assignment_id: int,
    user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed view of a specific assignment for the current student."""
    student = await _get_student(db, user.id)

    assignment_result = await db.execute(
        select(Assignment, Class.name)
        .join(Class, Assignment.class_id == Class.id)
        .where(Assignment.id == assignment_id)
    )
    assignment_row = assignment_result.first()
    if not assignment_row:
        raise HTTPException(status_code=404, detail="Assignment not found")
    assignment, class_name = assignment_row

    enrolled = await db.execute(
        select(ClassEnrollment.id).where(
            ClassEnrollment.student_id == student.id,
            ClassEnrollment.class_id == assignment.class_id
        )
    )
    if not enrolled.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Not enrolled in this class")

    sa_result = await db.execute(
        select(StudentAssignment).where(
            StudentAssignment.student_id == student.id,
            StudentAssignment.assignment_id == assignment_id
        )
    )
    sa = sa_result.scalar_one_or_none()

    exercises_result = await db.execute(
        select(AssignmentExercise, Exercise)
        .join(Exercise, AssignmentExercise.exercise_id == Exercise.id)
        .where(AssignmentExercise.assignment_id == assignment_id)
        .order_by(AssignmentExercise.order_index)
    )

    exercise_list = []
    for (ae, exercise) in exercises_result.all():
        any_correct_result = await db.execute(
            select(ExerciseAttempt.id)
            .where(ExerciseAttempt.student_id == student.id)
            .where(ExerciseAttempt.exercise_id == exercise.id)
            .where(ExerciseAttempt.correct == True)
            .limit(1)
        )
        has_correct = any_correct_result.scalar_one_or_none() is not None

        any_attempt_result = await db.execute(
            select(ExerciseAttempt.id)
            .where(ExerciseAttempt.student_id == student.id)
            .where(ExerciseAttempt.exercise_id == exercise.id)
            .limit(1)
        )
        has_any = any_attempt_result.scalar_one_or_none() is not None

        if has_correct:
            status = "correct"
        elif has_any:
            status = "in_progress"
        else:
            status = "not_started"

        exercise_list.append(ExerciseInAssignment(
            id=exercise.id,
            title=exercise.title,
            exercise_type=exercise.exercise_type,
            difficulty=exercise.difficulty,
            order_index=ae.order_index,
            status=status,
        ))

    total = len(exercise_list)
    correct_count = sum(1 for e in exercise_list if e.status == "correct")
    completion_rate = correct_count / total if total > 0 else 0.0

    return StudentAssignmentDetail(
        id=assignment.id,
        title=assignment.title,
        description=assignment.description,
        due_date=assignment.due_date,
        class_id=assignment.class_id,
        class_name=class_name,
        score=sa.score if sa else None,
        completion_rate=round(completion_rate, 4),
        exercises=exercise_list,
    )


@router.get("/classes", response_model=list[MyClassItem])
async def get_my_classes(
    user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db),
):
    """Get all classes the student is enrolled in."""
    if user.role != "student":
        raise HTTPException(status_code=403, detail="Student only")
    student = await _get_student(db, user.id)

    result = await db.execute(
        select(Class, ClassEnrollment)
        .join(ClassEnrollment, ClassEnrollment.class_id == Class.id)
        .where(ClassEnrollment.student_id == student.id)
    )

    classes = []
    for (cls, enrollment) in result.all():
        classes.append(MyClassItem(
            id=cls.id,
            name=cls.name,
            subject=cls.subject,
            invite_code=cls.invite_code,
            enrolled_at=enrollment.enrolled_at,
        ))
    return classes


class LinkParentRequest(BaseModel):
    link_code: str


class LinkParentResponse(BaseModel):
    success: bool
    parent_name: str


@router.post("/link-parent", response_model=LinkParentResponse)
async def link_parent_account(
    data: LinkParentRequest,
    user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db),
):
    """Student enters a 6-char code to link to their parent."""
    if user.role != UserRole.student:
        raise HTTPException(status_code=403, detail="Only students can link to parents")

    student = await _get_student(db, user.id)
    code = data.link_code.strip().upper()
    if not code:
        raise HTTPException(status_code=400, detail="Código requerido")

    # Find unclaimed link with this code
    link_result = await db.execute(
        select(ParentStudentLink).where(
            ParentStudentLink.link_code == code,
            ParentStudentLink.student_id == None,
        )
    )
    link = link_result.scalar_one_or_none()
    if not link:
        raise HTTPException(status_code=400, detail="Código inválido o ya usado")

    # Claim the link
    link.student_id = student.id
    await db.commit()

    # Get parent name
    parent_result = await db.execute(select(Parent).where(Parent.id == link.parent_id))
    parent = parent_result.scalar_one_or_none()
    parent_name = parent.user.name if parent else "Familiar"

    return LinkParentResponse(success=True, parent_name=parent_name)


async def _get_student(db: AsyncSession, user_id: int) -> Student:
    result = await db.execute(select(Student).where(Student.user_id == user_id))
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")
    return student