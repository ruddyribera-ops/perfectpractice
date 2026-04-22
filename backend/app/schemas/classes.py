from pydantic import BaseModel

class ClassJoinResponse(BaseModel):
    message: str
    class_name: str
    subject: str
