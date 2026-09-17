# app/schemas/api.py
from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    history: Optional[List[Dict[str, Any]]] = []


class ChatResponse(BaseModel):
    reply: str
    history: List[Dict[str, Any]]


class JobResponse(BaseModel):
    id: int
    title: Optional[str]
    company: Optional[str]
    location: Optional[str]
    remote_ok: bool
    stipend: Optional[str]
    required_skills: Optional[List[str]] = []
    experience_level: Optional[str]
    deadline: Optional[str]
    category: Optional[str] = "General Tech" # <-- ADD THIS
    source_url: str

    class Config:
        from_attributes = True

class MatchItemResponse(BaseModel):
    job_id: int
    title: Optional[str]
    company: Optional[str]
    location: Optional[str]
    remote_ok: bool
    stipend: Optional[str] = None
    category: Optional[str] = "General Tech" # <-- ADD THIS
    match_score: str
    required_skills: Optional[List[str]] = []
    justification: str
    source_url: str


class ResumeMatchResponse(BaseModel):
    success: bool
    matched_count: int
    matches: List[MatchItemResponse]