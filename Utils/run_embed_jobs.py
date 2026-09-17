import time
from app.db.session import SessionLocal
from app.models.job import JobListing
from app.services.embedding import get_embedding


def create_job_embedding_text(job: JobListing) -> str:
    """
    High-density semantic representation.
    Combines structured skills, role, and core description for high-signal retrieval.
    """
    skills_str = ", ".join(job.required_skills or [])
    location_info = f"{job.location} (Remote: {job.remote_ok})"
    
    return (
        f"Job Title: {job.title}\n"
        f"Company: {job.company}\n"
        f"Location: {location_info}\n"
        f"Experience Level: {job.experience_level}\n"
        f"Required Skills: {skills_str}\n"
        f"Description Snippet: {job.raw_content[:6500]}"
    )


def embed_all_jobs():
    db = SessionLocal()
    try:
        # Find jobs that are extracted but have no embedding yet
        jobs_to_embed = db.query(JobListing).filter(
            JobListing.is_extracted == True,
            JobListing.embedding == None
        ).all()

        print(f"[*] Found {len(jobs_to_embed)} jobs ready to be embedded...")

        if not jobs_to_embed:
            print("[✓] All extracted jobs already have embeddings!")
            return

        for idx, job in enumerate(jobs_to_embed, 1):
            print(f"[{idx}/{len(jobs_to_embed)}] Embedding: '{job.title}' at '{job.company}'")
            
            # 1. Create representation text
            text_to_embed = create_job_embedding_text(job)
            
            # 2. Call Gemini embedding model
            vector = get_embedding(text_to_embed, task_type="RETRIEVAL_DOCUMENT")
            
            # 3. Store vector in PostgreSQL pgvector column
            job.embedding = vector
            db.commit()

            # Small polite pause to stay under rate limits
            time.sleep(0.5)

        print(f"\n[✓] Successfully embedded and saved {len(jobs_to_embed)} jobs into pgvector!")

    finally:
        db.close()


if __name__ == "__main__":
    embed_all_jobs()