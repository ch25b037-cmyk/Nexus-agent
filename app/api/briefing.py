# app/api/briefing.py
import uuid
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User, BriefingJob
from app.services.briefing import run_briefing_pipeline

router = APIRouter(prefix="/api", tags=["Briefing"])

@router.post("/briefing/generate", status_code=status.HTTP_202_ACCEPTED)
async def trigger_briefing(background_tasks: BackgroundTasks, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    job_id = str(uuid.uuid4())
    db.add(BriefingJob(id=job_id, user_id=current_user.id, status="queued"))
    db.commit()

    background_tasks.add_task(run_briefing_pipeline, job_id=job_id, user_id=current_user.id, user_email=current_user.email)
    return {"job_id": job_id, "status": "queued", "message": "Briefing generation queued."}


@router.get("/briefing/status/{job_id}")
def check_briefing_status(job_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    job = db.query(BriefingJob).filter(BriefingJob.id == job_id, BriefingJob.user_id == current_user.id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Briefing job not found.")
    return {"job_id": job.id, "status": job.status, "media_url": job.media_url, "script": job.script, "error": job.error_message}


@router.get("/me/briefings")
def list_my_briefings(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    jobs = db.query(BriefingJob).filter(BriefingJob.user_id == current_user.id).order_by(BriefingJob.created_at.desc()).all()
    return [{"job_id": j.id, "status": j.status, "media_url": j.media_url, "created_at": j.created_at} for j in jobs]

# In app/api/briefing.py:

@router.delete("/briefing/{job_id}", tags=["Briefing"])
def delete_briefing(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Deletes a briefing. Anti-IDOR: strictly enforces user_id == current_user.id."""
    job = db.query(BriefingJob).filter(
        BriefingJob.id == job_id,
        BriefingJob.user_id == current_user.id
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="Briefing not found.")

    db.delete(job)
    db.commit()
    return {"message": "Briefing deleted successfully."}