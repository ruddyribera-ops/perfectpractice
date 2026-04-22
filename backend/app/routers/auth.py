from fastapi import APIRouter, Depends, HTTPException, Cookie
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
import hashlib
from datetime import datetime, timedelta, timezone

from app.core.database import get_db
from app.core.security import get_password_hash, verify_password, create_access_token, create_refresh_token, decode_token, get_current_user_required
from app.models.user import User, Student, Teacher, Session
from app.models.parent import Parent
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, UserResponse, ChangePasswordRequest

router = APIRouter()


@router.post("/register", response_model=TokenResponse)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(email=data.email, password_hash=get_password_hash(data.password), name=data.name, role=data.role if data.role in ("teacher", "parent") else "student")
    db.add(user)
    await db.flush()

    if data.role == "teacher":
        teacher = Teacher(user_id=user.id, school_name=data.school_name)
        db.add(teacher)
    elif data.role == "parent":
        parent = Parent(user_id=user.id)
        db.add(parent)
    else:
        student = Student(user_id=user.id, grade=data.grade or 1)
        db.add(student)

    await db.commit()
    await db.refresh(user)

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    await _create_session(db, user.id, refresh_token)

    return TokenResponse(user=UserResponse.model_validate(user), access_token=access_token, refresh_token=refresh_token)


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    await _create_session(db, user.id, refresh_token)

    return TokenResponse(user=UserResponse.model_validate(user), access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh")
async def refresh(refresh_token: Optional[str] = Cookie(None), db: AsyncSession = Depends(get_db)):
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token required")

    payload = decode_token(refresh_token, is_refresh=True)
    user_id = int(payload.get("sub"))
    token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()

    session_result = await db.execute(select(Session).where(Session.user_id == user_id, Session.token_hash == token_hash))
    session = session_result.scalar_one_or_none()

    if not session or session.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    return {"access_token": create_access_token({"sub": str(user_id)})}


@router.post("/logout")
async def logout(refresh_token: Optional[str] = Cookie(None), db: AsyncSession = Depends(get_db)):
    if refresh_token:
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        await db.execute(select(Session).where(Session.token_hash == token_hash).delete())
        await db.commit()
    return {"message": "Logged out"}


async def _create_session(db: AsyncSession, user_id: int, token: str):
    session = Session(user_id=user_id, token_hash=hashlib.sha256(token.encode()).hexdigest(), expires_at=datetime.now(timezone.utc) + timedelta(days=7))
    db.add(session)
    await db.commit()


@router.post("/change-password")
async def change_password(
    data: ChangePasswordRequest,
    user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db),
):
    """Change password for current user."""
    if not verify_password(data.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    if verify_password(data.new_password, user.password_hash):
        raise HTTPException(status_code=400, detail="New password must be different from current password")

    user.password_hash = get_password_hash(data.new_password)
    # Revoke all existing refresh token sessions — user must re-login everywhere
    await db.execute(
        select(Session).where(Session.user_id == user.id).delete()
    )
    await db.commit()
    return {"message": "Password changed successfully"}