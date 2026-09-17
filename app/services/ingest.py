# app/services/ingest.py
from sqlalchemy.orm import Session
from app.models.job import JobListing
from app.schemas.job import RawJobScrape


def store_raw_job(db: Session, raw_job: RawJobScrape) -> bool:
    """
    Tier 1 Deduplication & Storage:
    Checks if the job's url_hash already exists in the database.
    - Returns True if inserted as a new job.
    - Returns False if skipped as a duplicate.
    """
    # 1. Fast O(log N) B-Tree index lookup on url_hash
    existing = db.query(JobListing.id).filter(
        JobListing.url_hash == raw_job.url_hash
    ).first()

    if existing:
        return False  # Duplicate found, skip!

    # 2. Insert new record with is_extracted=False
    db_job = JobListing(
        url_hash=raw_job.url_hash,
        content_hash=raw_job.content_hash,
        source_url=raw_job.source_url,
        scraped_at=raw_job.scraped_at,
        raw_content=raw_job.raw_content,
        is_extracted=False
    )
    db.add(db_job)
    db.commit()
    return True