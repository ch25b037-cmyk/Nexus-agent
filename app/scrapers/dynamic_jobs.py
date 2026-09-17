# app/scrapers/dynamic_jobs.py
import re
from typing import List
import httpx
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

from app.scrapers.base import BaseScraper
from app.schemas.job import RawJobScrape
from app.utils.hasher import normalize_url, generate_content_hash


def _extract_clean_text(html: str) -> str:
    """Helper to strip boilerplate tags and return visible text."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "noscript", "svg"]):
        tag.decompose()
    return soup.body.get_text(separator="\n", strip=True) if soup.body else ""


class AICollegeJobsScraper(BaseScraper):
    """
    Source 2: Domain-Agnostic Adaptive Dynamic Scraper.
    Parses Markdown tables and uses an Adaptive Escalation strategy in Playwright:
    - Fast path for lightweight portals (1-2s).
    - Adaptive hydration escalation for heavy client-side SPAs if initial render is empty.
    - Graceful fallback to table metadata if portal is inaccessible.
    """
    REPO_URL = "https://raw.githubusercontent.com/speedyapply/2027-SWE-College-Jobs/refs/heads/main/README.md"

    def scrape(self, max_pages: int = 1) -> List[RawJobScrape]:
        print(f"[*] [Source 2] Fetching curated job listings from GitHub repository...")
        
        try:
            with httpx.Client(headers=self.headers, timeout=15.0, follow_redirects=True) as client:
                resp = client.get(self.REPO_URL)
                resp.raise_for_status()
                raw_markdown = resp.text
        except httpx.HTTPError as e:
            print(f"[!] Failed to fetch GitHub repo: {e}")
            return []

        lines = raw_markdown.splitlines()
        table_rows = [line.strip() for line in lines if line.strip().startswith("|") and line.strip().endswith("|")]

        print(f"[*] Found {len(table_rows)} listings in Markdown. Launching Adaptive Playwright...")

        scraped_jobs: List[RawJobScrape] = []
        company_counts = {}
        MAX_PER_COMPANY = 3
        TARGET_JOBS = 50

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )
            page = context.new_page()

            # Iterate through the table rows until we get 15 diverse jobs
            for row in table_rows[:100]:
                if len(scraped_jobs) >= TARGET_JOBS:
                    break

                cols = [c.strip() for c in row.split("|")[1:-1]]
                if len(cols) < 5:
                    continue

                clean_company = re.sub(r"<[^>]+>", "", cols[0]).strip()
                clean_role = re.sub(r"<[^>]+>", "", cols[1]).strip()
                clean_location = re.sub(r"<[^>]+>", "", cols[2]).strip()
                salary_raw = re.sub(r"<[^>]+>", "", cols[3]).strip()
                apply_col = cols[4]
                age_raw = re.sub(r"<[^>]+>", "", cols[5]).strip() if len(cols) > 5 else "Recent"

                # DIVERSITY GUARD: Skip if we already have 2 jobs from this company!
                if company_counts.get(clean_company, 0) >= MAX_PER_COMPANY:
                    continue

                url_match = re.search(r'href=["\'](https?://[^"\']+)["\']', apply_col)
                if not url_match:
                    continue

                clean_url = normalize_url(url_match.group(1))

                # Skip TikTok entirely if it blocks headless browsers
                if "lifeattiktok.com" in clean_url:
                    continue

                print(f"\n[{len(scraped_jobs) + 1}/{TARGET_JOBS}] Visiting: {clean_company} - {clean_role[:35]}...")

                detailed_description = ""
                try:
                    page.goto(clean_url, timeout=12000, wait_until="domcontentloaded")
                    page.wait_for_timeout(1500)
                    body_text = _extract_clean_text(page.content())

                    if len(body_text) < 150:
                        print(f"      [~] Minimal text. Escalating: waiting for SPA hydration...")
                        page.wait_for_timeout(4500)
                        body_text = _extract_clean_text(page.content())

                    if len(body_text) >= 150:
                        detailed_description = body_text[:8000]
                        print(f"      [✓] Extracted {len(detailed_description)} chars of detailed description!")
                    else:
                        print(f"      [!] Using structured metadata fallback.")
                        detailed_description = f"Actively hiring for {clean_role} at {clean_company}. Location: {clean_location}. Compensation: {salary_raw}."

                except PlaywrightTimeoutError:
                    print(f"      [!] Timeout. Using fallback.")
                    detailed_description = f"Actively hiring for {clean_role} at {clean_company}. Location: {clean_location}. Compensation: {salary_raw}."
                except Exception as err:
                    print(f"      [!] Error. Using fallback.")
                    detailed_description = f"Actively hiring for {clean_role} at {clean_company}. Location: {clean_location}. Compensation: {salary_raw}."

                synthesized_content = (
                    f"Company: {clean_company}\n"
                    f"Role Title: {clean_role}\n"
                    f"Location: {clean_location}\n"
                    f"Compensation / Stipend: {salary_raw}\n"
                    f"Application Timeline: Active (Timeline: {clean_role}, Posted {age_raw} ago)\n"
                    f"Application Link: {clean_url}\n"
                    f"Detailed Job Description:\n{detailed_description}"
                )

                job_scrape = RawJobScrape(
                    source_url=clean_url,
                    url_hash=generate_content_hash(clean_url),
                    content_hash=generate_content_hash(synthesized_content),
                    raw_content=synthesized_content
                )
                scraped_jobs.append(job_scrape)
                company_counts[clean_company] = company_counts.get(clean_company, 0) + 1

            browser.close()

        print(f"\n[✓] Source 2: Successfully scraped {len(scraped_jobs)} diverse dynamic jobs!")
        return scraped_jobs