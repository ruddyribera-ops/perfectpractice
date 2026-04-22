from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func

from app.core.database import Base


class ClassroomSync(Base):
    """
    Stores Google Classroom OAuth tokens and course linkage for each teacher.

    Each teacher can link one or more Google Classroom courses to their
    local classes. The tokens allow us to push assignments and sync topics.
    """
    __tablename__ = "classroom_syncs"

    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=False)
    # Google Classroom course ID (e.g. "1234567890")
    classroom_course_id = Column(String(100), nullable=False)
    # Name at time of linking (cached, not live)
    classroom_course_name = Column(String(255), nullable=False)
    # Optional link to our local class (NULL until teacher links explicitly)
    local_class_id = Column(Integer, ForeignKey("classes.id"), nullable=True)
    # OAuth tokens
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=False)
    token_expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())