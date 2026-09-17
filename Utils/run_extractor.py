# run_extraction.py
import time
from app.db.session import SessionLocal
from app.models.job import JobListing
from app.services.extractor import extract_job_details


def run_extraction_pipeline(limit: int = 5):
    """
    Pulls unextracted jobs from the database, runs LLM structuring,
    and updates the records.
    `limit=5` allows testing with a small batch first!
    """
    db = SessionLocal()
    try:
        # Caching check: only fetch jobs that haven't been extracted yet!
        pending_jobs = db.query(JobListing).filter(
            JobListing.is_extracted == False
        ).limit(limit).all()

        print(f"[*] Found {len(pending_jobs)} unextracted jobs waiting in DB...")

        if not pending_jobs:
            print("[✓] All listings are already extracted! No LLM calls needed.")
            return

        success_count = 0
        for idx, job in enumerate(pending_jobs, 1):
            print(f"\n[{idx}/{len(pending_jobs)}] Processing: {job.source_url}")
            
            structured_data = extract_job_details(job.raw_content)

            if structured_data:
                # Update DB record with the structured values
                job.title = structured_data.title
                job.company = structured_data.company
                job.location = structured_data.location
                job.remote_ok = structured_data.remote_ok
                job.stipend = structured_data.stipend
                job.required_skills = structured_data.required_skills
                job.experience_level = structured_data.experience_level
                job.deadline = structured_data.deadline
                job.is_extracted = True  # Marks extraction complete (caching)

                db.commit()
                success_count += 1
                print(f"  [✓] Extracted: '{job.title}' at '{job.company}'")
                print(f"      Skills: {job.required_skills}")
                print(f"      Remote: {job.remote_ok} | Exp: {job.experience_level}")
            else:
                print(f"  [✗] Skipped: Extraction rejected for {job.source_url}")

            # Polite 1-second delay to stay well within Groq free rate limits
            time.sleep(1.5)

        print(f"\n[✓] Batch complete! Successfully extracted {success_count}/{len(pending_jobs)} jobs.")

    finally:
        db.close()


if __name__ == "__main__":
    # Test with 3 jobs first to verify everything runs cleanly
    run_extraction_pipeline(limit=100)