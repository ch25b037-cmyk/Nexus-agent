from app.db.session import engine, Base
# Important: importing the model registers it with Base.metadata
from app.models.job import JobListing


def test_and_create_tables():
    print("[*] Connecting to Supabase PostgreSQL...")
    try:
        with engine.connect() as conn:
            print("[✓] Successfully connected to PostgreSQL!")
            
        print("[*] Creating tables (including pgvector columns)...")
        Base.metadata.create_all(bind=engine)
        print("[✓] Tables successfully created in Supabase!")
        
    except Exception as e:
        print(f"[!] Database connection failed: {e}")


if __name__ == "__main__":
    test_and_create_tables()