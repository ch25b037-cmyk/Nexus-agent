# app/agent/tools.py
from collections import Counter
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.job import JobListing
from app.services.embedding import get_embedding


def search_jobs_semantic(db: Session, query: str, limit: int = 3) -> List[Dict[str, Any]]:
    """
    Tool 1: Semantic vector search using pgvector.
    Finds jobs matching a tech stack, topic, or query.
    """
    try:
        query_vector = get_embedding(query, task_type="RETRIEVAL_QUERY")
        distance_col = JobListing.embedding.cosine_distance(query_vector).label("distance")

        results = db.query(JobListing, distance_col).filter(
            JobListing.embedding != None
        ).order_by(distance_col.asc()).limit(limit).all()

        jobs_data = []
        for job, distance in results:
            similarity = max(0.0, 1.0 - float(distance))
            jobs_data.append({
                "job_id": job.id,
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "remote_ok": job.remote_ok,
                "match_score": f"{round(similarity * 100, 1)}%",
                "skills": job.required_skills or [],
                "source_url": job.source_url
            })
        return jobs_data
    except Exception as e:
        return [{"error": f"Semantic search failed: {str(e)}"}]


def get_top_skills(db: Session, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Tool 2: Aggregates required_skills across the database.
    Directly answers: 'What skill appears most often?'
    """
    records = db.query(JobListing.required_skills).filter(
        JobListing.required_skills != None
    ).all()

    counter = Counter()
    for (skills,) in records:
        if skills:
            for s in skills:
                counter[s.strip()] += 1

    return [{"skill": skill, "count": count} for skill, count in counter.most_common(limit)]


def get_job_by_id(db: Session, job_id: int) -> Dict[str, Any]:
    """
    Tool 3: Fetches complete details and URL for a specific job ID.
    """
    job = db.query(JobListing).filter(JobListing.id == job_id).first()
    if not job:
        return {"error": f"No job found with ID {job_id}."}

    return {
        "job_id": job.id,
        "title": job.title,
        "company": job.company,
        "location": job.location,
        "remote_ok": job.remote_ok,
        "stipend": job.stipend,
        "experience_level": job.experience_level,
        "deadline": job.deadline or "Not specified",
        "skills": job.required_skills or [],
        "source_url": job.source_url,
        "summary": job.raw_content[:400]
    }

# In app/agent/tools.py:

# ---------------------------------------------------------
# Tool 4: Parametric / Category Filtering
# ---------------------------------------------------------
def filter_jobs_parametric(
    db: Session, 
    category: Optional[str] = None, 
    remote_only: bool = False, 
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Tool: Exact relational filtering by category and remote status.
    """
    query = db.query(JobListing).filter(JobListing.is_extracted == True)

    if category and category.lower() != "all":
        # Case-insensitive substring match on category
        query = query.filter(JobListing.category.ilike(f"%{category}%"))
    
    if remote_only:
        query = query.filter(JobListing.remote_ok == True)

    jobs = query.limit(limit).all()
    if not jobs:
        return [{"message": f"No listings found matching category='{category}', remote={remote_only}."}]

    return [{
        "job_id": j.id,
        "title": j.title,
        "company": j.company,
        "category": j.category,
        "location": j.location,
        "remote_ok": j.remote_ok,
        "stipend": j.stipend,
        "skills": j.required_skills or []
    } for j in jobs]


# ---------------------------------------------------------
# Tool 5: Personalized Skill Gap Analysis
# ---------------------------------------------------------
def analyze_skill_gap(
    db: Session, 
    job_id: int, 
    candidate_skills: List[str]
) -> Dict[str, Any]:
    """
    Tool: Compares candidate skills against a specific job's requirements.
    Calculates skill match percentage and identifies missing skills.
    """
    job = db.query(JobListing).filter(JobListing.id == job_id).first()
    if not job:
        return {"error": f"Job with ID {job_id} not found."}

    req_skills = [s.strip() for s in (job.required_skills or [])]
    if not req_skills:
        return {"message": "This job does not specify strict skill prerequisites."}

    cand_set = {s.lower().strip() for s in candidate_skills}
    
    matching = []
    missing = []

    for s in req_skills:
        s_low = s.lower()
        if any(c in s_low or s_low in c for c in cand_set):
            matching.append(s)
        else:
            missing.append(s)

    match_pct = round((len(matching) / len(req_skills)) * 100, 1) if req_skills else 100.0

    return {
        "job_id": job.id,
        "title": job.title,
        "company": job.company,
        "total_required_skills": len(req_skills),
        "matching_skills": matching,
        "missing_skills": missing,
        "skill_coverage": f"{match_pct}%",
        "verdict": "Strong Skill Fit" if match_pct >= 60 else "Skill Gap Identified"
    }


# ---------------------------------------------------------
# Tool 6: Highest Paying Opportunities
# ---------------------------------------------------------
def get_highest_paying_roles(db: Session, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Tool: Retrieves top compensation listings from the database.
    """
    jobs = db.query(JobListing).filter(
        JobListing.is_extracted == True,
        JobListing.stipend != None
    ).order_by(JobListing.id.desc()).limit(limit).all()

    return [{
        "job_id": j.id,
        "title": j.title,
        "company": j.company,
        "category": j.category,
        "stipend": j.stipend,
        "location": j.location,
        "remote_ok": j.remote_ok,
        "url": j.source_url
    } for j in jobs]