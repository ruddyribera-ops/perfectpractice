from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
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
    __table_args__ = (
        # Prevent the same student from being linked to the same parent twice
        UniqueConstraint('parent_id', 'student_id', name='uq_parent_student_link'),
    )


class ParentActivity(Base):
    __tablename__ = "parent_activities"
    id = Column(Integer, primary_key=True, index=True)
    grade = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(String, nullable=False)
    materials = Column(String, nullable=False, default="Lápiz y papel")
    estimated_minutes = Column(Integer, nullable=False, default=15)
    difficulty = Column(String(20), nullable=False, default="medium")
    bar_model_topic = Column(String(255), nullable=True)
    topic_id = Column(Integer, nullable=True)
    day_index = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ParentActivityCompletion(Base):
    __tablename__ = "parent_activity_completions"
    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, ForeignKey("parents.id"), nullable=False)
    activity_id = Column(Integer, ForeignKey("parent_activities.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    completed_at = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        UniqueConstraint('parent_id', 'activity_id', 'student_id', name='uq_parent_activity_student'),
    )