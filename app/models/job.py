# app/models/job.py
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.dialects.postgresql import ARRAY
from pgvector.sqlalchemy import Vector

from app.db.session import Base


class JobListing(Base):
    __tablename__ = "job_listings"

    id = Column(Integer, primary_key=True, index=True)
    
    # --- Deduplication & Provenance (Section 4.2) ---
    url_hash = Column(String(64), unique=True, index=True, nullable=False)
    content_hash = Column(String(64), index=True, nullable=False)
    source_url = Column(Text, nullable=False)
    scraped_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # --- Raw Content Storage ---
    raw_content = Column(Text, nullable=False)

    # --- Structured Fields (Section 4.2) ---
    is_extracted = Column(Boolean, default=False, index=True)
    title = Column(String(255), nullable=True, index=True)
    company = Column(String(255), nullable=True, index=True)
    location = Column(String(255), nullable=True)
    remote_ok = Column(Boolean, default=False)
    stipend = Column(String(100), nullable=True)
    required_skills = Column(ARRAY(String), nullable=True)
    category = Column(String(100), default="General Tech", index=True) # <-- ADD THIS!
    experience_level = Column(String(100), nullable=True)
    deadline = Column(String(100), nullable=True)

    # --- Vector Embeddings (Section 4.2 Requirement 3) ---
    embedding = Column(Vector(768), nullable=True)

    def __repr__(self):
        return f"<JobListing id={self.id} title='{self.title}' company='{self.company}'>"