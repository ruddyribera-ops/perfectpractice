from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.core.database import get_db
from app.core.security import get_current_user_required
from app.models.user import User, Student
from app.models.notification import Notification
from app.schemas.notification import NotificationResponse, NotificationListResponse

router = APIRouter()


@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    read_filter: str = Query("all", pattern="^(all|read|unread)$"),
):
    # Base query filtered by user
    base_query = select(Notification).where(Notification.user_id == user.id)
    if read_filter == "read":
        base_query = base_query.where(Notification.read == True)
    elif read_filter == "unread":
        base_query = base_query.where(Notification.read == False)

    # Total count
    count_q = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_q)
    total = total_result.scalar() or 0

    # Unread count (always across all notifications for this user)
    unread_q = select(func.count()).where(
        Notification.user_id == user.id,
        Notification.read == False,
    )
    unread_result = await db.execute(unread_q)
    unread_count = unread_result.scalar() or 0

    # Paginated, ordered by created_at DESC
    offset = (page - 1) * limit
    paged_query = (
        base_query
        .order_by(desc(Notification.created_at))
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(paged_query)
    items = result.scalars().all()

    pages = (total + limit - 1) // limit if limit > 0 else 0

    return NotificationListResponse(
        items=[NotificationResponse.model_validate(n) for n in items],
        total=total,
        unread_count=unread_count,
        page=page,
        pages=pages,
    )


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_read(
    notification_id: int,
    user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user.id,
        )
    )
    notification = result.scalar_one_or_none()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    notification.read = True
    await db.commit()
    await db.refresh(notification)
    return NotificationResponse.model_validate(notification)


@router.post("/mark-all-read")
async def mark_all_notifications_read(
    user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Notification).where(
            Notification.user_id == user.id,
            Notification.read == False,
        )
    )
    unread = result.scalars().all()
    updated = len(unread)
    for n in unread:
        n.read = True
    if unread:
        await db.commit()

    return {"success": True, "updated": updated}


async def _get_student(db: AsyncSession, user_id: int) -> Student:
    result = await db.execute(select(Student).where(Student.user_id == user_id))
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")
    return student
