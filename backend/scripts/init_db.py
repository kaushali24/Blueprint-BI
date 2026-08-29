"""
Initialize the SQLite database and seed the required MVP Business record.
Safe to run multiple times (idempotent).
"""
import sys
from pathlib import Path

# Add backend directory to sys.path to allow running from root or scripts dir
sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.database.base import Base
from app.database.connection import engine, SessionLocal
from app.database.models import Business

def init_db():
    print("Creating database schema...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Check if MVP Business already exists
        business = db.get(Business, 1)
        if business is None:
            print("Seeding MVP Business (Nadeeka Cakes)...")
            business = Business(
                id=1,
                name="Nadeeka Cakes",
                slug="nadeeka-cakes"
            )
            db.add(business)
            db.commit()
            print("Successfully seeded Business record.")
        else:
            print(f"Business record already exists (id={business.id}, name='{business.name}'). Skipping seed.")
    except Exception as e:
        print(f"Error during initialization: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()
    
    print("Database initialization complete.")

if __name__ == "__main__":
    init_db()
