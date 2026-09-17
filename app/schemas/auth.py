# app/schemas/auth.py
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr
from app.schemas.api import JobResponse


class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_email: str


class ShortlistSaveRequest(BaseModel):
    job_id: int
    match_score: Optional[str] = None
    justification: Optional[str] = None


class ShortlistItemResponse(BaseModel):
    id: int
    job_id: int
    match_score: Optional[str]
    justification: Optional[str]
    saved_at: datetime
    job: JobResponse

    class Config:
        from_attributes = True