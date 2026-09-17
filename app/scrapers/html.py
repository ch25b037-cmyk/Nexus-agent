# app/scrapers/html_board.py
import time
from urllib.parse import urljoin
import httpx
from bs4 import BeautifulSoup
from typing import List

from app.scrapers.base import BaseScraper
from app.schemas.job import RawJobScrape
from app.utils.hasher import normalize_url, generate_content_hash


class PythonOrgScraper(BaseScraper):
    """
    Scraper for Python.org Jobs (Source 1: Paginated HTML Board).
    """
    BASE_URL = "https://www.python.org/jobs/"

    def scrape(self, max_pages: int =3 ) -> List[RawJobScrape]:
        scraped_jobs: List[RawJobScrape] = []
        seen_hashes = set()

        with httpx.Client(headers=self.headers, timeout=10.0, follow_redirects=True) as client:
            for page in range(1, max_pages + 1):
                page_url = f"{self.BASE_URL}?page={page}"
                print(f"[*] Fetching page {page}: {page_url}")

                try:
                    resp = client.get(page_url)
                    resp.raise_for_status()
                except httpx.HTTPError as e:
                    print(f"[!] Error fetching {page_url}: {e}")
                    break

                soup = BeautifulSoup(resp.text, "html.parser")

                # On python.org/jobs, listings are in <ol class="list-recent-jobs"> -> <li>
                job_list = soup.find("ol", class_="list-recent-jobs")
                if not job_list:
                    print("[!] No job list found on page. Ending pagination.")
                    break

                listing_tags = job_list.find_all("li")
                if not listing_tags:
                    print("[!] Empty listings on page. Ending pagination.")
                    break

                for item in listing_tags:
                    # Each <li> has an <h2> or <span> with an <a> link to the job details
                    link_tag = item.find("a", href=True)
                    if not link_tag:
                        continue

                    job_detail_url = urljoin(self.BASE_URL, link_tag["href"])
                    clean_url = normalize_url(job_detail_url)

                    # --- Tier 1 Deduplication check in-memory ---
                    if clean_url in seen_hashes:
                        print(f"[-] Skipping duplicate URL: {clean_url}")
                        continue

                    # Polite rate limit before fetching the detailed job page
                    time.sleep(self.delay_seconds)

                    # Now fetch the actual job detail page
                    raw_job = self._scrape_detail_page(client, clean_url)
                    if raw_job:
                        seen_hashes.add(clean_url)
                        scraped_jobs.append(raw_job)

        print(f"[✓] Completed scraping. Total raw jobs gathered: {len(scraped_jobs)}")
        return scraped_jobs

    def _scrape_detail_page(self, client: httpx.Client, url: str) -> RawJobScrape | None:
        """
        Fetches an individual job description page and strips irrelevant tags.
        """
        try:
            resp = client.get(url)
            resp.raise_for_status()
        except httpx.HTTPError as e:
            print(f"[!] Failed to fetch details for {url}: {e}")
            return None

        soup = BeautifulSoup(resp.text, "html.parser")

        # python.org/jobs detailed content is inside <div class="job-description">
        # If not found, fallback to the main content container
        # Initial Mistake - content_box = soup.find("div", class_="job-description") or soup.find("article") or soup.body
        # Grabs the full article container with <h1> company name + description
        content_box = soup.find("article", class_="text") or soup.find("main") or soup.find("div", class_="job-description") or soup.body

        if not content_box:
            return None

        # Clean out boilerplates
        for tag in content_box(["script", "style", "nav", "footer", "form"]):
            tag.decompose()

        clean_text = content_box.get_text(separator="\n", strip=True)

        return RawJobScrape(
            source_url=url,
            url_hash=generate_content_hash(url),
            content_hash=generate_content_hash(clean_text),
            raw_content=clean_text[:6000]  # Store up to 6,000 chars for LLM context
        )