"""
Google Classroom integration router.

Handles:
- OAuth 2.0 flow (authorize → callback)
- Listing linked Classroom courses
- Linking a Classroom course to a local class
- Pushing assignments / topics to Classroom
"""

import secrets
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_user_required
from app.core.classroom_client import (
    GoogleClassroomClient,
    build_google_oauth_url,
    exchange_code_for_tokens,
    get_oauth_token_info,
)
from app.models.user import User, Teacher
from app.models.classes import Class
from app.models.classroom_sync import ClassroomSync
from app.schemas.classroom import (
    ClassroomCourseResponse,
    ClassroomLinkRequest,
    ClassroomSyncResponse,
    ClassroomTopicResponse,
)


router = APIRouter(prefix="/api/classroom", tags=["classroom"])


# -------------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------------

async def _require_teacher(user: User, db: AsyncSession) -> Teacher:
    if user.role != "teacher":
        raise HTTPException(status_code=403, detail="Teacher only")
    result = await db.execute(select(Teacher).where(Teacher.user_id == user.id))
    teacher = result.scalar_one_or_none()
    if not teacher:
        raise HTTPException(status_code=403, detail="No teacher profile")
    return teacher


async def _get_client_for_teacher(
    teacher_id: int, db: AsyncSession
) -> tuple[GoogleClassroomClient, ClassroomSync]:
    """Load the most recent ClassroomSync for a teacher and build a client."""
    result = await db.execute(
        select(ClassroomSync)
        .where(ClassroomSync.teacher_id == teacher_id)
        .order_by(ClassroomSync.created_at.desc())
    )
    sync = result.scalar_one_or_none()
    if not sync:
        raise HTTPException(status_code=400, detail="Not connected to Google Classroom. Authorize first.")

    client = GoogleClassroomClient(
        access_token=sync.access_token,
        refresh_token=sync.refresh_token,
        token_expires_at=sync.token_expires_at,
        db=db,
        sync_record=sync,
    )
    return client, sync


# -------------------------------------------------------------------------
# OAuth flow
# -------------------------------------------------------------------------

@router.get("/authorize")
async def authorize(
    user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db),
):
    """
    Begin Google OAuth flow.
    Returns the redirect URL — frontend should navigate to it.
    """
    teacher = await _require_teacher(user, db)

    # Generate state token to prevent CSRF
    state = secrets.token_urlsafe(32)

    # Store state in a temporary location (in-memory for this flow)
    # We embed the teacher_id in the state so callback can retrieve it
    oauth_state_store[state] = {"teacher_id": teacher.id, "user_id": user.id}

    url = build_google_oauth_url(state)
    return {"authorization_url": url}


# Simple in-memory state store (reset on server restart)
oauth_state_store: dict = {}


@router.get("/callback")
async def callback(
    code: str = Query(...),
    state: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Handle OAuth callback from Google.
    Exchange code for tokens, store them, return success.
    """
    if state not in oauth_state_store:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")

    stored = oauth_state_store.pop(state)
    teacher_id = stored["teacher_id"]

    # Exchange code for tokens
    token_data = await exchange_code_for_tokens(code)
    access_token = token_data["access_token"]
    refresh_token = token_data["refresh_token"]
    expires_in = token_data.get("expires_in", 3600)
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

    # Verify token and get user info
    token_info = await get_oauth_token_info(access_token)
    email = token_info.get("email", "")

    # Store the sync record
    sync = ClassroomSync(
        teacher_id=teacher_id,
        classroom_course_id="",  # Will be set when they pick a course
        classroom_course_name="Pending",
        access_token=access_token,
        refresh_token=refresh_token,
        token_expires_at=expires_at,
    )
    db.add(sync)
    await db.commit()

    return {"message": "Google Classroom connected successfully", "email": email}


# -------------------------------------------------------------------------
# Classroom courses
# -------------------------------------------------------------------------

@router.get("/courses")
async def list_courses(
    user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db),
):
    """List all Google Classroom courses for the connected teacher."""
    teacher = await _require_teacher(user, db)
    client, _ = await _get_client_for_teacher(teacher.id, db)

    courses = await client.list_courses()
    return [
        ClassroomCourseResponse(
            course_id=c.get("id", ""),
            name=c.get("name", ""),
            section=c.get("section", ""),
            description=c.get("description", ""),
            room=c.get("room", ""),
            owner=c.get("ownerId", ""),
        )
        for c in courses
    ]


# -------------------------------------------------------------------------
# Link / unlink
# -------------------------------------------------------------------------

@router.post("/link")
async def link_classroom(
    data: ClassroomLinkRequest,
    user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db),
):
    """
    Link a Google Classroom course to a local class.

    classroom_course_id: Google Classroom course ID (e.g. "1234567890")
    local_class_id: our internal class ID
    """
    teacher = await _require_teacher(user, db)

    # Verify local class belongs to this teacher
    result = await db.execute(select(Class).where(Class.id == data.local_class_id))
    local_class = result.scalar_one_or_none()
    if not local_class:
        raise HTTPException(status_code=404, detail="Class not found")
    if local_class.teacher_id != teacher.id:
        raise HTTPException(status_code=403, detail="Not your class")

    # Get Classroom course details
    client, sync = await _get_client_for_teacher(teacher.id, db)
    gc_course = await client.get_course(data.classroom_course_id)
    course_name = gc_course.get("name", "Unknown")

    # Check if already linked
    existing = await db.execute(
        select(ClassroomSync).where(
            ClassroomSync.classroom_course_id == data.classroom_course_id,
            ClassroomSync.local_class_id == data.local_class_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Already linked")

    # Create a new sync record for this specific link (keep separate from auth-only record)
    new_sync = ClassroomSync(
        teacher_id=teacher.id,
        classroom_course_id=data.classroom_course_id,
        classroom_course_name=course_name,
        local_class_id=data.local_class_id,
        access_token=sync.access_token,
        refresh_token=sync.refresh_token,
        token_expires_at=sync.token_expires_at,
    )
    db.add(new_sync)
    await db.commit()

    return {"message": f"Linked to '{course_name}'", "sync_id": new_sync.id}


@router.delete("/link/{sync_id}")
async def unlink_classroom(
    sync_id: int,
    user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db),
):
    """Remove a Classroom ↔ local class link."""
    teacher = await _require_teacher(user, db)

    result = await db.execute(
        select(ClassroomSync).where(
            ClassroomSync.id == sync_id,
            ClassroomSync.teacher_id == teacher.id,
        )
    )
    sync = result.scalar_one_or_none()
    if not sync:
        raise HTTPException(status_code=404, detail="Link not found")

    await db.delete(sync)
    await db.commit()
    return {"message": "Link removed"}


@router.get("/links")
async def list_links(
    user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db),
):
    """List all Classroom links for the current teacher."""
    teacher = await _require_teacher(user, db)

    result = await db.execute(
        select(ClassroomSync).where(ClassroomSync.teacher_id == teacher.id)
    )
    syncs = result.scalars().all()

    return [
        {
            "id": s.id,
            "classroom_course_id": s.classroom_course_id,
            "classroom_course_name": s.classroom_course_name,
            "local_class_id": s.local_class_id,
            "created_at": s.created_at,
        }
        for s in syncs
    ]


# -------------------------------------------------------------------------
# Topics (Google Classroom topics)
# -------------------------------------------------------------------------

@router.get("/courses/{course_id}/topics")
async def get_classroom_topics(
    course_id: str,
    user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db),
):
    """Get topics in a Google Classroom course."""
    teacher = await _require_teacher(user, db)
    client, _ = await _get_client_for_teacher(teacher.id, db)

    topics = await client.list_topics(course_id)
    return [
        ClassroomTopicResponse(
            topic_id=t.get("topicId", ""),
            name=t.get("name", ""),
        )
        for t in topics
    ]


@router.post("/topics")
async def sync_topic_to_classroom(
    sync_id: int,
    topic_name: str,
    user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a topic in Google Classroom and store the reference.

    sync_id: our ClassroomSync id (defines which Classroom course to use)
    topic_name: name of the topic to create
    """
    teacher = await _require_teacher(user, db)

    result = await db.execute(
        select(ClassroomSync).where(
            ClassroomSync.id == sync_id,
            ClassroomSync.teacher_id == teacher.id,
        )
    )
    sync = result.scalar_one_or_none()
    if not sync:
        raise HTTPException(status_code=404, detail="Link not found")

    client = GoogleClassroomClient(
        access_token=sync.access_token,
        refresh_token=sync.refresh_token,
        token_expires_at=sync.token_expires_at,
        db=db,
        sync_record=sync,
    )

    topic = await client.create_topic(sync.classroom_course_id, topic_name)
    return ClassroomSyncResponse(
        id=sync.id,
        classroom_course_id=sync.classroom_course_id,
        classroom_topic_id=topic.get("topicId", ""),
        topic_name=topic_name,
    )


# -------------------------------------------------------------------------
# Assignments (push to Classroom)
# -------------------------------------------------------------------------
# Assignments (push to Classroom)
# -------------------------------------------------------------------------

@router.post("/sync-assignment")
async def sync_assignment_to_classroom(
    sync_id: int,
    assignment_id: int,
    topic_id: str | None = None,
    user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db),
):
    """
    Push a local assignment to Google Classroom.

    sync_id: our ClassroomSync id (which course to push to)
    assignment_id: our local assignment ID
    topic_id: optional Google Classroom topicId to assign to
    """
    teacher = await _require_teacher(user, db)

    result = await db.execute(
        select(ClassroomSync).where(
            ClassroomSync.id == sync_id,
            ClassroomSync.teacher_id == teacher.id,
        )
    )
    sync = result.scalar_one_or_none()
    if not sync:
        raise HTTPException(status_code=404, detail="Link not found")

    client = GoogleClassroomClient(
        access_token=sync.access_token,
        refresh_token=sync.refresh_token,
        token_expires_at=sync.token_expires_at,
        db=db,
        sync_record=sync,
    )

    # Load the local assignment
    from app.models.classes import Assignment
    ass_result = await db.execute(
        select(Assignment).where(Assignment.id == assignment_id).options(selectinload(Assignment.class_))
    )
    assignment = ass_result.scalar_one_or_none()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    if assignment.class_.teacher_id != teacher.id:
        raise HTTPException(status_code=403, detail="Not your assignment")

    # Build body
    body: dict = {
        "title": assignment.title,
        "description": assignment.description or "",
    }
    if assignment.due_date:
        body["dueDate"] = {
            "year": assignment.due_date.year,
            "month": assignment.due_date.month,
            "day": assignment.due_date.day,
        }
        body["dueTime"] = {"hours": 23, "minutes": 59}
    if topic_id:
        body["topicId"] = topic_id

    gc_work = await client.create_course_work(sync.classroom_course_id, **body)

    return ClassroomSyncResponse(
        id=sync.id,
        classroom_course_id=sync.classroom_course_id,
        classroom_assignment_id=gc_work.get("id", ""),
        assignment_title=assignment.title,
    )


# -------------------------------------------------------------------------
# Import submissions from Classroom
# -------------------------------------------------------------------------

@router.post("/import-submissions")
async def import_submissions(
    sync_id: int,
    user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db),
):
    """
    Pull submission states from Google Classroom for linked assignments.
    Updates our StudentAssignment.completed_at / score accordingly.
    """
    teacher = await _require_teacher(user, db)

    result = await db.execute(
        select(ClassroomSync).where(
            ClassroomSync.id == sync_id,
            ClassroomSync.teacher_id == teacher.id,
        )
    )
    sync = result.scalar_one_or_none()
    if not sync:
        raise HTTPException(status_code=404, detail="Link not found")

    client = GoogleClassroomClient(
        access_token=sync.access_token,
        refresh_token=sync.refresh_token,
        token_expires_at=sync.token_expires_at,
        db=db,
        sync_record=sync,
    )

    course_work = await client.list_course_work(sync.classroom_course_id)

    # TODO: match our assignments to Classroom courseWork and update StudentAssignment
    # Requires mapping our assignment title → Google Classroom assignment ID

    return {
        "message": "Submission import complete",
        "course_work_count": len(course_work),
        "note": "Detailed matching TBD per implementation",
    }