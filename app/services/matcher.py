# app/services/matcher.py
import io
from typing import List, Dict, Any
from pypdf import PdfReader
from sqlalchemy.orm import Session
from groq import Groq
import os
from dotenv import load_dotenv
from fastapi import Depends
from typing import Optional 

from app.models.job import JobListing
from app.services.embedding import get_embedding
from app.utils.cost_tracker import track_tokens
from app.models.user import User
from app.api.deps import get_current_user


load_dotenv()
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def extract_text_from_pdf(pdf_source) -> str:
    """
    Extracts raw text from a PDF file path or file-like bytes buffer.
    """
    if isinstance(pdf_source, (bytes, bytearray)):
        reader = PdfReader(io.BytesIO(pdf_source))
    else:
        reader = PdfReader(pdf_source)

    full_text = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            full_text.append(text)

    cleaned = "\n".join(full_text).strip()
    return cleaned


def generate_match_justification(resume_snippet: str, job: JobListing, user_id : Optional[int] = None) -> str:
    """
    Uses Groq to generate a crisp, 1-line justification for why the listing matches.
    """
    prompt = f"""You are a career intelligence advisor.
In exactly ONE concise sentence (max 25 words), explain why this job matches the candidate's profile.

Candidate Profile Snippet:
{resume_snippet[:1000]}

Job Title: {job.title} at {job.company}
Required Skills: {', '.join(job.required_skills or [])}
Job Summary: {job.raw_content[:500]}

Write ONLY the one-line justification. No quotes, no preamble.
"""
    try:
        completion = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="openai/gpt-oss-120b",
            temperature=0.2,
            max_tokens=500
        )
        track_tokens("extraction", "openai/gpt-oss-120b", getattr(completion, "usage", None), user_id=user_id)

        return completion.choices[0].message.content.strip()
    except Exception as e:
        return f"Matches candidate profile based on technical skill alignment."


def match_resume_to_jobs(db: Session, resume_text: str, top_k: int = 5, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    1. Generates embedding for the resume.
    2. Runs pgvector cosine distance search against job_listings.
    3. Fetches top_k matches.
    4. Generates a 1-line LLM justification for each match.
    """
    # 1. Generate resume query vector
    resume_vector = get_embedding(resume_text, task_type="RETRIEVAL_QUERY")

    # 2. Query PostgreSQL pgvector using Cosine Distance (<=>)
    # Cosine distance: 0 = identical, 1 = orthogonal, 2 = opposite
    # Cosine similarity = 1 - cosine_distance
    distance_col = JobListing.embedding.cosine_distance(resume_vector).label("distance")

    results = db.query(JobListing, distance_col).filter(
        JobListing.embedding != None
    ).order_by(distance_col.asc()).limit(top_k).all()

    matches = []
    for job, distance in results:
        # Convert distance to similarity percentage
        similarity = max(0.0, 1.0 - float(distance))
        match_percentage = round(similarity * 100, 1)

        # 3. Generate the 1-line justification
        justification = generate_match_justification(resume_text, job, user_id = user_id)

        matches.append({
            "job_id": job.id,
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "remote_ok": job.remote_ok,
            "stipend": job.stipend,
            "category": job.category or "General Tech",
            "match_score": f"{match_percentage}%",
            "required_skills": job.required_skills,
            "justification": justification,
            "source_url": job.source_url
        })

    return matches