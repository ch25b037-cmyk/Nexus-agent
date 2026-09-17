# test_matching.py
from app.db.session import SessionLocal
from app.services.matcher import match_resume_to_jobs

# Sample resume text representing a student developer
SAMPLE_RESUME = """
Gokkul - Software Engineering Student
Technical Skills:
- Languages: Python, JavaScript, SQL
- Frameworks & Tools: FastAPI, Docker, PostgreSQL, Git, Linux
- Areas of Interest: Backend engineering, asynchronous programming, building REST APIs, vector databases
- Projects: Built an autonomous web scraper and career intelligence agent using pgvector and LLMs.
"""

def main():
    print("[*] Testing Resume Semantic Matching with pgvector...")
    db = SessionLocal()
    try:
        matches = match_resume_to_jobs(db, SAMPLE_RESUME, top_k=3)
        
        print(f"\n[✓] Found Top {len(matches)} Matches:\n")
        for idx, match in enumerate(matches, 1):
            print(f"{idx}. {match['title']} at {match['company']}")
            print(f"   Match Score:   {match['match_score']}")
            print(f"   Remote:        {match['remote_ok']}")
            print(f"   Skills:        {match['required_skills']}")
            print(f"   Justification: {match['justification']}")
            print(f"   URL:           {match['source_url']}\n")

    finally:
        db.close()

if __name__ == "__main__":
    main()