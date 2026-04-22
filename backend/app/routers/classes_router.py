from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user_required
from app.models.user import User, Student
from app.models.classes import Class, ClassEnrollment
from app.schemas.classes import ClassJoinResponse

router = APIRouter()

@router.post("/join/{invite_code}", response_model=ClassJoinResponse)
async def join_class(invite_code: str, user: User = Depends(get_current_user_required), db: AsyncSession = Depends(get_db)):
    if user.role != "student":
        raise HTTPException(status_code=403, detail="Students only")
    result = await db.execute(select(Class).where(Class.invite_code == invite_code))
    class_ = result.scalar_one_or_none()
    if not class_:
        raise HTTPException(status_code=404, detail="Class not found")
    student_result = await db.execute(select(Student).where(Student.user_id == user.id))
    student = student_result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")
    existing = await db.execute(select(ClassEnrollment).where(ClassEnrollment.student_id == student.id, ClassEnrollment.class_id == class_.id))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Already enrolled in this class")
    enrollment = ClassEnrollment(student_id=student.id, class_id=class_.id)
    db.add(enrollment)
    await db.commit()
    return ClassJoinResponse(message=f"Successfully joined {class_.name}", class_name=class_.name, subject=class_.subject)
