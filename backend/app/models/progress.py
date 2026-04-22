from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, ForeignKey, Boolean, JSON, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base

class ExerciseAttempt(Base):
    __tablename__ = "exercise_attempts"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    exercise_id = Column(Integer, ForeignKey("exercises.id"), nullable=False)
    assignment_id = Column(Integer, ForeignKey("assignments.id"), nullable=True)
    answer_json = Column(JSON, nullable=False)
    correct = Column(Boolean, nullable=False)
    points_earned = Column(Integer, default=0)
    xp_earned = Column(Integer, default=0)
    time_spent_seconds = Column(Integer, default=0)
    attempted_at = Column(DateTime(timezone=True), server_default=func.now())
    student = relationship("Student", back_populates="exercise_attempts")
    exercise = relationship("Exercise", back_populates="attempts")

class StudentTopicProgress(Base):
    __tablename__ = "student_topic_progress"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False)
    exercises_completed = Column(Integer, default=0)
    total_exercises = Column(Integer, default=0)
    mastery_score = Column(Float, default=0.0)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    student = relationship("Student", back_populates="topic_progress")
    topic = relationship("Topic")
