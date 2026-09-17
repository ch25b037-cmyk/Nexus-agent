# app/scrapers/base.py
from abc import ABC, abstractmethod
from typing import List
from app.schemas.job import RawJobScrape


class BaseScraper(ABC):
    """
    Abstract base scraper that all source scrapers must implement.
    Guarantees standard polite behavior, user agents, and output format.
    """
    def __init__(self, delay_seconds: float = 1.0):
        self.delay_seconds = delay_seconds
        self.headers = {
            "User-Agent": "NexusCareerAgent/1.0 (Recruitment Demo; polite-bot)"
        }

    @abstractmethod
    def scrape(self, max_pages: int = 2) -> List[RawJobScrape]:
        """
        Scrapes job listings and returns standardized RawJobScrape models.
        """
        pass