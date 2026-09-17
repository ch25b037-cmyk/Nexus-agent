# test_scraper.py
from app.scrapers.html import PythonOrgScraper

if __name__ == "__main__":
    print("--- Testing HTML Scraper ---")
    scraper = PythonOrgScraper(delay_seconds=1.0)
    
    # Scrape just 1 page to test fast
    results = scraper.scrape(max_pages=1)
    
    print(f"\nSuccessfully scraped {len(results)} jobs!\n")
    
    if results:
        sample = results[0]
        print(f"Sample Job URL: {sample.source_url}")
        print(f"URL Hash: {sample.url_hash}")
        print(f"Scraped At: {sample.scraped_at}")
        print("\n--- Raw Content Preview (First 400 chars) ---")
        print(sample.raw_content[:8000])
        print("---------------------------------------------")