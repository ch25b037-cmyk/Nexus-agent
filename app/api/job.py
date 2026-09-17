# app/api/jobs.py
from typing import List, Optional
from collections import Counter
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.job import JobListing
from app.schemas.api import JobResponse
from app.agent.tools import get_top_skills

router = APIRouter(prefix="/api/jobs", tags=["Jobs"])

@router.get("", response_model=List[JobResponse])
def list_jobs(category: Optional[str] = None, skip: int = 0, limit: int = 102, db: Session = Depends(get_db)):
    query = db.query(JobListing).filter(JobListing.is_extracted == True)
    if category and category != "All":
        query = query.filter(JobListing.category == category)
    return query.offset(skip).limit(limit).all()


@router.get("/skills")
def top_skills(limit: int = 10, db: Session = Depends(get_db)):
    return get_top_skills(db, limit=limit)


@router.get("/categories")
def get_categories(db: Session = Depends(get_db)):
    records = db.query(JobListing.category).filter(JobListing.is_extracted == True).all()
    counter = Counter([r[0] for r in records if r[0]])
    return [{"category": cat, "count": count} for cat, count in counter.most_common()]


@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(JobListing).filter(JobListing.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    return job