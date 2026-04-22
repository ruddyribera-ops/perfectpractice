from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: str = "student"
    grade: Optional[int] = None
    school_name: Optional[str] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    role: str
    created_at: datetime
    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    user: UserResponse
    access_token: str
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
