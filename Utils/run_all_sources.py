# run_all_sources.py
from app.db.session import SessionLocal
from app.scrapers.html import PythonOrgScraper
from app.scrapers.dynamic_jobs import AICollegeJobsScraper
from app.services.ingest import store_raw_job


def main():
    print("=" * 60)
    print("🚀 NEXUS Multi-Source Ingestion Engine")
    print("Source 1: Static HTML DOM (python.org)")
    print("Source 2: Hybrid Dynamic Playwright + Markdown (AI College Jobs)")
    print("=" * 60)
    
    scrapers = [
        ("Source 1: Python.org (Static HTML)", PythonOrgScraper(delay_seconds=1.0)),
        ("Source 2: Top Tech Jobs (Playwright Headless)", AICollegeJobsScraper())
    ]

    db = SessionLocal()
    total_new = 0
    total_skipped = 0

    try:
        for name, scraper in scrapers:
            print(f"\n---> Running {name}...")
            jobs = scraper.scrape()
            
            source_new = 0
            source_skipped = 0
            for j in jobs:
                if store_raw_job(db, j):
                    source_new += 1
                else:
                    source_skipped += 1

            print(f"     [Result] New: {source_new} | Deduplicated: {source_skipped}")
            total_new += source_new
            total_skipped += source_skipped

        print("\n" + "=" * 60)
        print(f"🎉 Pipeline Complete! Total New: {total_new} | Deduplicated: {total_skipped}")
        print("=" * 60)

    finally:
        db.close()


if __name__ == "__main__":
    main()