from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.core.database import Base

class ExerciseType(str, enum.Enum):
    multiple_choice = "multiple_choice"
    numeric = "numeric"
    true_false = "true_false"
    ordering = "ordering"
    bar_model = "bar_model"  # Singapore math visual problem solving
    word_problem = "word_problem"  # Multi-step real-world problems

class Difficulty(str, enum.Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"

class Topic(Base):
    __tablename__ = "topics"
    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    parent_id = Column(Integer, ForeignKey("topics.id"), nullable=True)
    icon_name = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    parent = relationship("Topic", remote_side=[id], back_populates="children")
    children = relationship("Topic", back_populates="parent")
    units = relationship("Unit", back_populates="topic")

class Unit(Base):
    __tablename__ = "units"
    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    order_index = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    topic = relationship("Topic", back_populates="units")
    exercises = relationship("Exercise", back_populates="unit")
    lessons = relationship("Lesson", back_populates="unit")

class Lesson(Base):
    __tablename__ = "lessons"
    id = Column(Integer, primary_key=True, index=True)
    unit_id = Column(Integer, ForeignKey("units.id"), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    content_type = Column(String(20), default="text", nullable=False)
    order_index = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    unit = relationship("Unit", back_populates="lessons")
    exercises = relationship("Exercise", back_populates="lesson")
    model_config = {"from_attributes": True}

class Exercise(Base):
    __tablename__ = "exercises"
    id = Column(Integer, primary_key=True, index=True)
    unit_id = Column(Integer, ForeignKey("units.id"), nullable=False)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=True)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    exercise_type = Column(SQLEnum(ExerciseType), default=ExerciseType.multiple_choice)
    difficulty = Column(SQLEnum(Difficulty), default=Difficulty.medium)
    points_value = Column(Integer, default=10)
    data = Column(JSON, nullable=False)
    hints = Column(JSON, nullable=True)
    is_anked = Column(Boolean, default=False)
    is_summative = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    unit = relationship("Unit", back_populates="exercises")
    lesson = relationship("Lesson", back_populates="exercises")
    attempts = relationship("ExerciseAttempt", back_populates="exercise")
