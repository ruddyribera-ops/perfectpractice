from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base

class Achievement(Base):
    __tablename__ = "achievements"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    badge_key = Column(String(100), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
    icon = Column(String(100), nullable=True)
    earned_at = Column(DateTime(timezone=True), server_default=func.now())
    student = relationship("Student", back_populates="achievements")

class LeaderboardCache(Base):
    __tablename__ = "leaderboard_cache"
    id = Column(Integer, primary_key=True, index=True)
    scope = Column(String(50), nullable=False)
    period = Column(String(50), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    rank = Column(Integer, nullable=False)
    points = Column(Integer, default=0)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    student = relationship("Student")
