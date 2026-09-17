# app/services/scheduler.py
import datetime
from apscheduler.schedulers.background import BackgroundScheduler

from app.db.session import SessionLocal
from app.scrapers.html import PythonOrgScraper
from app.scrapers.dynamic_jobs import AICollegeJobsScraper
from app.services.ingest import store_raw_job
from app.services.extractor import extract_job_details
from app.services.embedding import get_embedding
from app.models.job import JobListing

# Global scheduler instance
scheduler = BackgroundScheduler()


def autonomous_crawl_and_refresh():
    """
    Scheduled Job:
    1. Re-scrapes public sources.
    2. Ingests new unique listings (deduped via SHA-256).
    3. Runs LLM structured extraction on newly discovered jobs.
    4. Generates dense 768-dim embeddings in pgvector.
    5. Categorizes newly inserted listings.
    """
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n" + "=" * 60)
    print(f"⏰ [CRON JOB STARTED: {now_str}] Autonomous Web Ingestion")
    print("=" * 60)

    db = SessionLocal()
    scrapers = [
        ("Source 1: Python.org", PythonOrgScraper(delay_seconds=1.0)),
        ("Source 2: Top Tech Jobs (Playwright)", AICollegeJobsScraper())
    ]

    new_jobs_count = 0
    try:
        # Step 1: Run scrapers & deduplicate
        for name, scraper in scrapers:
            print(f"[*] Cron crawling {name}...")
            jobs = scraper.scrape()
            for j in jobs:
                if store_raw_job(db, j):
                    new_jobs_count += 1

        print(f"[✓] Cron Ingestion complete. Discovered {new_jobs_count} new listings.")

        # Step 2: Extract structured fields for any new unextracted rows
        unextracted = db.query(JobListing).filter(JobListing.is_extracted == False).all()
        if unextracted:
            print(f"[*] Extracting {len(unextracted)} new jobs with Groq...")
            for job in unextracted:
                structured = extract_job_details(job.raw_content)
                if structured:
                    job.title = structured.title
                    job.company = structured.company
                    job.location = structured.location
                    job.remote_ok = structured.remote_ok
                    job.stipend = structured.stipend
                    job.required_skills = structured.required_skills
                    job.experience_level = structured.experience_level
                    job.deadline = structured.deadline or "Rolling Basis (Active)"
                    job.is_extracted = True
                    db.commit()

        # Step 3: Compute pgvector embeddings for any rows missing vectors
        unembedded = db.query(JobListing).filter(
            JobListing.is_extracted == True,
            JobListing.embedding == None
        ).all()
        if unembedded:
            print(f"[*] Generating pgvector embeddings for {len(unembedded)} listings...")
            for job in unembedded:
                skills_str = ", ".join(job.required_skills or [])
                text = (
                    f"Job Title: {job.title}\n"
                    f"Company: {job.company}\n"
                    f"Location: {job.location}\n"
                    f"Required Skills: {skills_str}\n"
                    f"Description:\n{job.raw_content[:6500]}"
                )
                job.embedding = get_embedding(text, task_type="RETRIEVAL_DOCUMENT")
                db.commit()

        print(f"🎉 [CRON JOB FINISHED] All data refreshed and synchronized with pgvector!")
        print("=" * 60 + "\n")

    except Exception as e:
        print(f"[!] Cron Job Error: {e}")
    finally:
        db.close()


def start_scheduler(interval_hours: int = 12):
    """Starts the background scheduler daemon."""
    if not scheduler.running:
        scheduler.add_job(
            autonomous_crawl_and_refresh,
            trigger="cron",
            hour="0,12",
            id="autonomous_crawler_job",
            name="Periodic Ingestion & Vector Refresh",
            replace_existing=True
        )
        scheduler.start()
        print(f"[✓] APScheduler initialized! Autonomous crawl running every {interval_hours} hours.")