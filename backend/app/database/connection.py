from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


# backend/
BASE_DIR = Path(__file__).resolve().parents[2]

# backend/data/blueprint.db
DATABASE_PATH = BASE_DIR / "data" / "blueprint.db"

DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)