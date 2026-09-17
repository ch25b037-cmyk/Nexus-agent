# app/services/briefing.py
import os
import asyncio
from typing import List, Dict, Any, Optional
import httpx
import edge_tts
from dotenv import load_dotenv
from groq import Groq
from sqlalchemy.orm import Session
from fastapi import Depends

from app.db.session import SessionLocal
from app.models.user import BriefingJob, UserResume, UserSavedJob
from app.models.job import JobListing
from app.services.matcher import match_resume_to_jobs
from app.utils.cost_tracker import track_tokens
from app.api.deps import get_current_user

load_dotenv()

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
HEYGEN_API_KEY = os.getenv("HEYGEN_API_KEY")
LLM_MODEL = "openai/gpt-oss-120b"

STATIC_DIR = os.path.join(os.getcwd(), "static", "briefings")
os.makedirs(STATIC_DIR, exist_ok=True)


def generate_briefing_script(user_email: str, jobs_data: List[Dict[str, Any]], source_type: str = "matches",user_id: Optional[int] = Depends(get_current_user)   # <-- Add user_id!
) -> str:
    """
    Generates a spoken executive briefing script strictly grounded in real JobListing database records.
    `source_type` is one of: 'shortlist', 'matches', or 'featured'.
    """
    user_name = user_email.split("@")[0].capitalize()

    print(f"\n[DIAGNOSTIC] === Step 1: Script Generation ===")
    print(f"  User: {user_name} ({user_email})")
    print(f"  Source Type: {source_type} ({len(jobs_data)} real job listings provided)")

    # Build rich context directly from JobListing fields
    listings_context = ""
    for idx, j in enumerate(jobs_data[:3], 1):
        skills = ", ".join(j.get("skills", [])[:5]) if j.get("skills") else "Core Engineering"
        stipend_info = f"Compensation: {j.get('stipend')}" if j.get("stipend") else "Compensation: Competitive"
        deadline_info = f"Deadline: {j.get('deadline')}" if j.get("deadline") else "Timeline: Active Rolling Basis"
        why_match = f"Why it fits: {j.get('justification')}" if j.get("justification") else "High-impact opportunity."

        listings_context += (
            f"Opportunity {idx}:\n"
            f"  - Title: {j.get('title')}\n"
            f"  - Company: {j.get('company')}\n"
            f"  - Location: {j.get('location')} (Remote: {j.get('remote_ok')})\n"
            f"  - {stipend_info}\n"
            f"  - {deadline_info}\n"
            f"  - Key Skills: {skills}\n"
            f"  - {why_match}\n\n"
        )

    prompt = f"""You are an executive career advisor delivering a personalized morning intelligence briefing for {user_name}.
Write an energetic, concise, professional spoken script (120-140 words, ~60 seconds).

Candidate Name: {user_name}
Context: Delivering briefing based on {source_type}.

Target Job Listings (FROM LIVE DATABASE):
{listings_context}

SCRIPT REQUIREMENTS:
1. Start with an upbeat greeting: "Hello {user_name}, here is your NEXUS Career Intelligence briefing."
2. Explicitly mention the top 2-3 companies, their exact roles, and specific details (e.g. mention the compensation like $63/hr or location if available).
3. Connect the requirements or skills (e.g. Python, Deep Learning) to why they should apply.
4. Conclude with an inspiring call to action: "Review these listings on your dashboard, and let NEXUS know when you're ready to apply. Keep building!"
5. Output ONLY the raw spoken text. Do NOT include stage directions, speaker labels, or markdown formatting.
"""

    try:
        completion = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=LLM_MODEL,
            temperature=0.3,
            max_tokens=2000,
            
        )
        track_tokens("briefing", LLM_MODEL, getattr(completion, "usage", None), user_id=user_id.id)
        script = completion.choices[0].message.content.strip()
        print(f"  [✓] LLM Script Generated ({len(script)} chars):")
        print(f"      \"{script[:150]}...\"")
        return script
    except Exception as e:
        print(f"  [!] LLM Script Generation Error: {e}. Using grounded fallback.")
        top_comp = jobs_data[0].get("company") if jobs_data else "top tech teams"
        top_role = jobs_data[0].get("title") if jobs_data else "Software Engineer"
        return (
            f"Good morning {user_name}. Here is your NEXUS Career Intelligence briefing. "
            f"This week, our platform surfaced top opportunities, led by {top_role} at {top_comp}. "
            f"Review your listings on the dashboard, check the application links, and apply early. Keep building!"
        )


async def render_heygen_video(script: str) -> Optional[str]:
    """Submits script to HeyGen Avatar API and polls for completed video URL."""
    if not HEYGEN_API_KEY or HEYGEN_API_KEY.strip() == "":
        return None

    headers = {
        "x-api-key": HEYGEN_API_KEY.strip(),
        "Content-Type": "application/json"
    }

    payload = {
        "video_inputs": [
            {
                "character": {
                    "type": "avatar",
                    "avatar_id": "Daisy-inskirt-20220818",
                    "avatar_style": "normal"
                },
                "voice": {
                    "type": "text",
                    "input_text": script,
                    "voice_id": "1bd001e7e50f421d837fb814d08b2982"
                }
            }
        ],
        "dimension": {"width": 1280, "height": 720}
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.post("https://api.heygen.com/v2/video/generate", json=payload, headers=headers)
            data = resp.json()

            video_id = data.get("data", {}).get("video_id")
            if not video_id:
                return None

            for attempt in range(15):
                await asyncio.sleep(5)
                status_resp = await client.get(
                    f"https://api.heygen.com/v1/video_status.get?video_id={video_id}",
                    headers=headers
                )
                status_data = status_resp.json().get("data", {})
                if status_data.get("status") == "completed":
                    return status_data.get("video_url")
                elif status_data.get("status") == "failed":
                    return None
            return None
        except Exception:
            return None


async def render_audio_fallback(script: str, job_id: str) -> str:
    """Synthesizes audio via edge-tts."""
    filename = f"briefing_{job_id}.mp3"
    filepath = os.path.join(STATIC_DIR, filename)

    try:
        communicate = edge_tts.Communicate(script, "en-US-ChristopherNeural")
        await communicate.save(filepath)
        file_size = os.path.getsize(filepath) if os.path.exists(filepath) else 0
        print(f"  [✓] Audio written to disk: {filepath} ({file_size:,} bytes)")
    except Exception as e:
        print(f"  [!] Audio generation error: {e}")

    return f"/static/briefings/{filename}"


async def run_briefing_pipeline(job_id: str, user_id: int, user_email: str):
    """
    True Database-Grounded Worker:
    Pulls real JobListing records from Supabase (Shortlist -> Resume Matches -> Featured Listings).
    """
    print(f"\n" + "=" * 60)
    print(f"🚀 [BRIEFING PIPELINE START] Job ID: {job_id}")
    print(f"=" * 60)

    db: Session = SessionLocal()
    try:
        job = db.query(BriefingJob).filter(BriefingJob.id == job_id).first()
        if not job:
            return

        job.status = "processing"
        db.commit()

        jobs_to_brief = []
        source_type = "featured"

       # 1. PRIORITY 1: User's Uploaded Resume (Top Semantic Matches!)
        user_resume = db.query(UserResume).filter(UserResume.user_id == user_id).first()
        if user_resume and user_resume.raw_text:
            print(f"[*] Found user resume for User {user_id}. Generating personalized vector matches...")
            source_type = "your top personalized resume matches"
            matches = match_resume_to_jobs(db, user_resume.raw_text, top_k=3)
            for m in matches:
                db_job = db.query(JobListing).filter(JobListing.id == m["job_id"]).first()
                jobs_to_brief.append({
                    "title": m["title"],
                    "company": m["company"],
                    "location": m["location"],
                    "remote_ok": m["remote_ok"],
                    "stipend": db_job.stipend if db_job else None,
                    "deadline": db_job.deadline if db_job else None,
                    "skills": m.get("required_skills", []),
                    "justification": m.get("justification")
                })

        # 2. PRIORITY 2: User's Shortlist (Fallback if user hasn't uploaded a resume!)
        if not jobs_to_brief:
            shortlisted = db.query(UserSavedJob).filter(
                UserSavedJob.user_id == user_id
            ).order_by(UserSavedJob.saved_at.desc()).limit(3).all()

            if shortlisted:
                print(f"[*] User {user_id} has no resume, but found {len(shortlisted)} shortlisted jobs!")
                source_type = "your shortlisted roles"
                for item in shortlisted:
                    db_job = item.job
                    if db_job:
                        jobs_to_brief.append({
                            "title": db_job.title,
                            "company": db_job.company,
                            "location": db_job.location,
                            "remote_ok": db_job.remote_ok,
                            "stipend": db_job.stipend,
                            "deadline": db_job.deadline,
                            "skills": db_job.required_skills or [],
                            "justification": item.justification or "Saved in your personal shortlist."
                        })

        # 3. PRIORITY 3: Featured Listings (Empty State fallback)
        if not jobs_to_brief:
            print(f"[*] User {user_id} has no resume or shortlist. Using newest featured listings...")
            source_type = "featured market listings"
            featured = db.query(JobListing).filter(
                JobListing.is_extracted == True,
                JobListing.stipend != None
            ).order_by(JobListing.id.desc()).limit(3).all()

            for db_job in featured:
                jobs_to_brief.append({
                    "title": db_job.title,
                    "company": db_job.company,
                    "location": db_job.location,
                    "remote_ok": db_job.remote_ok,
                    "stipend": db_job.stipend,
                    "deadline": db_job.deadline,
                    "skills": db_job.required_skills or [],
                    "justification": f"Featured opportunity at {db_job.company}."
                })
           

        # Generate Script with real JobListing data
        script = generate_briefing_script(user_email, jobs_to_brief, source_type=source_type, user_id=user_id)        
        job.script = script
        db.commit()

        # Render Video or Audio
        media_url = await render_heygen_video(script)
        if not media_url:
            media_url = await render_audio_fallback(script, job_id)

        job.media_url = media_url
        job.status = "completed"
        db.commit()
        print(f"\n🎉 [BRIEFING COMPLETE] URL: {media_url}")

    except Exception as e:
        print(f"\n[!] Pipeline Error: {e}")
        job = db.query(BriefingJob).filter(BriefingJob.id == job_id).first()
        if job:
            job.status = "failed"
            job.error_message = str(e)
            db.commit()
    finally:
        db.close()