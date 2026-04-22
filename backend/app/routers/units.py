from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.curriculum import Unit
from app.schemas.curriculum import UnitDetailResponse

router = APIRouter()

@router.get("/{slug}", response_model=UnitDetailResponse)
async def get_unit(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Unit).where(Unit.slug == slug).options(selectinload(Unit.exercises), selectinload(Unit.lessons)))
    unit = result.scalar_one_or_none()
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    return UnitDetailResponse.model_validate(unit)
