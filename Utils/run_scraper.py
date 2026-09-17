# run_scraper.py
from app.db.session import SessionLocal
from app.scrapers.html import PythonOrgScraper
from app.services.ingest import store_raw_job


def main():
    print("[*] Starting Scraper Pipeline...")
    scraper = PythonOrgScraper(delay_seconds=1.0)
    
    # Scrape 1 page for a quick test
    scraped_items = scraper.scrape(max_pages=1)
    
    db = SessionLocal()
    inserted_count = 0
    skipped_count = 0

    try:
        for job in scraped_items:
            is_new = store_raw_job(db, job)
            if is_new:
                inserted_count += 1
                print(f"[+] Stored new listing: {job.source_url}")
            else:
                skipped_count += 1
                print(f"[-] Skipped existing listing (Deduplicated): {job.source_url}")

        print("\n==============================")
        print(f"Total Scraped: {len(scraped_items)}")
        print(f"New Inserted:  {inserted_count}")
        print(f"Deduplicated:  {skipped_count}")
        print("==============================")

    finally:
        db.close()


if __name__ == "__main__":
    main()