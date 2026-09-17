# app/api/shortlist.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User, UserSavedJob
from app.models.job import JobListing
from app.schemas.auth import ShortlistSaveRequest, ShortlistItemResponse

router = APIRouter(prefix="/api", tags=["Shortlist"])

@router.post("/shortlist")
def save_to_shortlist(req: ShortlistSaveRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    job = db.query(JobListing).filter(JobListing.id == req.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    existing = db.query(UserSavedJob).filter(UserSavedJob.user_id == current_user.id, UserSavedJob.job_id == req.job_id).first()
    if existing:
        return {"message": "Job already shortlisted", "shortlist_id": existing.id}

    saved_item = UserSavedJob(user_id=current_user.id, job_id=req.job_id, match_score=req.match_score, justification=req.justification)
    db.add(saved_item)
    db.commit()
    return {"message": "Saved to shortlist", "shortlist_id": saved_item.id}


@router.get("/me/shortlist", response_model=List[ShortlistItemResponse])
def get_my_shortlist(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(UserSavedJob).filter(UserSavedJob.user_id == current_user.id).order_by(UserSavedJob.saved_at.desc()).all()


@router.delete("/shortlist/{shortlist_id}")
def remove_from_shortlist(shortlist_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = db.query(UserSavedJob).filter(UserSavedJob.id == shortlist_id, UserSavedJob.user_id == current_user.id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found.")
    db.delete(item)
    db.commit()
    return {"message": "Removed from shortlist."}