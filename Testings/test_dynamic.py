# test_dynamic.py
from app.scrapers.dynamic_jobs import AICollegeJobsScraper

if __name__ == "__main__":
    print("--- Testing Source 2 (Playwright + Markdown Hybrid Scraper) ---")
    scraper = AICollegeJobsScraper()
    jobs = scraper.scrape()
    
    print(f"\nTotal jobs gathered: {len(jobs)}")
    if jobs:
        print("\n--- SAMPLE EXTRACTED JOB (First 600 chars) ---")
        print(jobs[0].raw_content[:600])
        print("-----------------------------------------------")