from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Parent(Base):
    __tablename__ = "parents"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    user = relationship("User", back_populates="parent")


class ParentStudentLink(Base):
    __tablename__ = "parent_student_links"
    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, ForeignKey("parents.id"), nullable=False)
    student_id = Column(Integer, nullable=True)  # NULL = unclaimed, set to student id when claimed
    link_code = Column(String(20), nullable=False, unique=True)  # 6-char code parent uses to link
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)