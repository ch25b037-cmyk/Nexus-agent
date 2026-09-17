from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class RawJobScrape(BaseModel):
    """
    Represents raw data extracted from the web scraper before LLM structuring.
    """
    source_url: str
    url_hash: str
    content_hash: str
    raw_content: str
    scraped_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class JobExtractionSchema(BaseModel):
    """
    The strict schema required by NEXUS specification (Section 4.2).
    """
    title: str = Field(description="The job or internship title, e.g. 'Backend Engineering Intern'")
    company: str = Field(description="Name of the hiring company or organization")
    location: Optional[str] = Field(default="Remote", description="City, country, or 'Remote'")
    remote_ok: bool = Field(default=False, description="True if remote work is permitted, False otherwise")
    stipend: Optional[str] = Field(default=None, description="Compensation or stipend details, e.g. '₹25,000/month' or '$80k/yr'")
    required_skills: List[str] = Field(default_factory=list, description="Extracted list of technical and soft skills")
    experience_level: str = Field(default="Not Specified", description="e.g. 'Internship', 'Entry Level', 'Mid-Level', 'Senior'")
    deadline: Optional[str] = Field(default=None, description="Application deadline if mentioned, or null")

    # --- Robustness Validators: Handling LLM Flakiness ---

    @field_validator("required_skills", mode="before")
    @classmethod
    def parse_skills(cls, v):
        """
        If LLM returns a single comma-separated string like 'Python, FastAPI, Docker',
        automatically convert it into a clean list of trimmed strings.
        """
        if isinstance(v, str):
            return [skill.strip() for skill in v.split(",") if skill.strip()]
        if isinstance(v, list):
            return [str(skill).strip() for skill in v if str(skill).strip()]
        return []

    @field_validator("title", "company", mode="before")
    @classmethod
    def fallback_unknown(cls, v):
        """Ensure title and company are never empty strings."""
        if not v or not str(v).strip():
            return "Unknown"
        return str(v).strip()

from app.schemas.job import JobExtractionSchema

# Simulating messy output returned by an LLM
messy_llm_json = {
    "title": " Backend Engineer ",
    "company": " Razorpay ",
    "location": "Bengaluru",
    "remote_ok": "true",                  # String instead of boolean!
    "stipend": "₹40,000/mo",
    "required_skills": "Python, FastAPI, Docker, SQL", # Comma-separated string instead of list!
    "experience_level": "Internship",
    "deadline": "2026-10-01"
}

validated_job = JobExtractionSchema.model_validate(messy_llm_json)
print(validated_job.model_dump_json(indent=2))    