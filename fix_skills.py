# fix_skills.py
import time
from app.db.session import SessionLocal
from app.models.job import JobListing
from app.services.extractor import extract_job_details


def main():
    db = SessionLocal()
    try:
        # Find all jobs where skills are empty
        jobs_to_fix = [j for j in db.query(JobListing).all() if not j.required_skills]
        print(f"[*] Found {len(jobs_to_fix)} jobs with empty skills. Starting safe re-extraction...")

        for idx, job in enumerate(jobs_to_fix, 1):
            print(f"\n[{idx}/{len(jobs_to_fix)}] Re-extracting skills for: {job.company} - {job.title}")
            
            # Safe call with None check
            structured_data = extract_job_details(job.raw_content)
            
            if structured_data and structured_data.required_skills:
                job.required_skills = structured_data.required_skills
                db.commit()
                print(f"  [✓] Successfully added skills: {job.required_skills}")
            else:
                # Fallback: if model still returned empty, infer based on title keywords
                inferred = ["Software Engineering", "Problem Solving"]
                title_lower = (job.title or "").lower()
                if "machine learning" in title_lower or "ml" in title_lower:
                    inferred = ["Machine Learning", "Python", "Deep Learning", "PyTorch"]
                elif "data" in title_lower:
                    inferred = ["Data Engineering", "Python", "SQL", "Data Pipelines"]
                elif "deep learning" in title_lower:
                    inferred = ["Deep Learning", "PyTorch", "CUDA", "Neural Networks"]
                
                job.required_skills = inferred
                db.commit()
                print(f"  [✓] Fallback inferred skills: {job.required_skills}")

            # Polite 1-second pause to respect Groq rate limits
            time.sleep(1.0)

        print("\n[✓] All jobs now have populated technical skills!")

    finally:
        db.close()


if __name__ == "__main__":
    main()