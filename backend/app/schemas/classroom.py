from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ClassroomCourseResponse(BaseModel):
    course_id: str
    name: str
    section: Optional[str] = ""
    description: Optional[str] = ""
    room: Optional[str] = ""
    owner: Optional[str] = ""


class ClassroomTopicResponse(BaseModel):
    topic_id: str
    name: str


class ClassroomLinkRequest(BaseModel):
    classroom_course_id: str
    local_class_id: int


class ClassroomSyncResponse(BaseModel):
    id: int
    classroom_course_id: str
    classroom_topic_id: Optional[str] = None
    classroom_assignment_id: Optional[str] = None
    topic_name: Optional[str] = None
    assignment_title: Optional[str] = None
    local_class_id: Optional[int] = None