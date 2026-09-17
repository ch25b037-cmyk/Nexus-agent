# app/api/resume.py
from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_optional_user
from app.models.user import User, UserResume
from app.schemas.api import ResumeMatchResponse
from app.services.matcher import extract_text_from_pdf, match_resume_to_jobs

router = APIRouter(prefix="/api/resume", tags=["Resume Matching"])

@router.post("/match", response_model=ResumeMatchResponse)
async def match_resume(
    file: UploadFile = File(...),
    top_k: int = 5,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid format. Upload PDF.")

    contents = await file.read()
    resume_text = extract_text_from_pdf(contents)

    if len(resume_text.strip()) < 50:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not extract text from PDF.")

    matches = match_resume_to_jobs(db, resume_text, top_k=top_k, user_id=current_user.id)

    if current_user:
        existing_resume = db.query(UserResume).filter(UserResume.user_id == current_user.id).first()
        if existing_resume:
            existing_resume.filename = file.filename
            existing_resume.raw_text = resume_text
        else:
            db.add(UserResume(user_id=current_user.id, filename=file.filename, raw_text=resume_text))
        db.commit()

    return {"success": True, "matched_count": len(matches), "matches": matches}