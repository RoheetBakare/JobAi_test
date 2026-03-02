from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, or_
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Job
from app.schemas import JobOut, JobStatusUpdate

router = APIRouter(prefix="/jobs", tags=["jobs"])

@router.get("", response_model=list[JobOut])
def list_jobs(
    status: Optional[str] = None,
    q: Optional[str] = None,
    location: Optional[str] = None,
    days_min: Optional[int] = None,  # e.g. 3
    days_max: Optional[int] = None,  # e.g. 7
    limit: int = 50,
    db: Session = Depends(get_db),
):
    stmt = select(Job)

    if status:
        stmt = stmt.where(Job.status == status)

    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(Job.title.ilike(like), Job.company.ilike(like)))

    if location:
        stmt = stmt.where(Job.location.ilike(f"%{location}%"))

    if days_min is not None and days_max is not None:
        now = datetime.utcnow()
        newest = now - timedelta(days=days_min)   # posted <= newest (not too new)
        oldest = now - timedelta(days=days_max)   # posted >= oldest (not too old)
        stmt = stmt.where(Job.posted_at.isnot(None)).where(Job.posted_at.between(oldest, newest))

    stmt = stmt.order_by(Job.posted_at.desc().nullslast()).limit(limit)
    return list(db.execute(stmt).scalars().all())

@router.patch("/{job_id}", response_model=JobOut)
def update_job_status(job_id: str, payload: JobStatusUpdate, db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    job.status = payload.status
    db.add(job)
    db.commit()
    db.refresh(job)
    return job