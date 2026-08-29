import pytest
from sqlalchemy import inspect

from app.database.models import Business, Base
from scripts.init_db import init_db

@pytest.fixture
def temp_db_engine(tmp_path, monkeypatch):
    """Provide a temporary database engine for testing init_db."""
    from sqlalchemy import create_engine
    
    temp_db_path = tmp_path / "test_init.db"
    temp_url = f"sqlite:///{temp_db_path}"
    test_engine = create_engine(temp_url)
    
    # Monkeypatch the engine and SessionLocal in init_db
    monkeypatch.setattr("scripts.init_db.engine", test_engine)
    
    from sqlalchemy.orm import sessionmaker
    TestSessionLocal = sessionmaker(bind=test_engine)
    monkeypatch.setattr("scripts.init_db.SessionLocal", TestSessionLocal)
    
    yield test_engine, TestSessionLocal

def test_init_db_creates_schema_and_business(temp_db_engine):
    engine, TestSessionLocal = temp_db_engine
    
    # 1. Verify db is empty
    inspector = inspect(engine)
    assert not inspector.has_table("business")
    
    # 2. Run init
    init_db()
    
    # 3. Verify schema created
    inspector = inspect(engine)
    assert inspector.has_table("business")
    assert inspector.has_table("message")
    
    # 4. Verify business created
    with TestSessionLocal() as db:
        business = db.get(Business, 1)
        assert business is not None
        assert business.name == "Nadeeka Cakes"
        assert business.slug == "nadeeka-cakes"

def test_init_db_is_idempotent(temp_db_engine):
    engine, TestSessionLocal = temp_db_engine
    
    # Run twice
    init_db()
    init_db()
    
    # Verify exactly one business
    with TestSessionLocal() as db:
        businesses = db.query(Business).all()
        assert len(businesses) == 1
        assert businesses[0].id == 1
        assert businesses[0].name == "Nadeeka Cakes"

def test_init_db_preserves_existing_data(temp_db_engine):
    engine, TestSessionLocal = temp_db_engine
    
    # 1. Setup existing db
    Base.metadata.create_all(bind=engine)
    with TestSessionLocal() as db:
        business = Business(id=1, name="Custom Name", slug="custom")
        db.add(business)
        db.commit()
        
    # 2. Run init_db
    init_db()
    
    # 3. Verify data wasn't overwritten
    with TestSessionLocal() as db:
        business = db.get(Business, 1)
        assert business.name == "Custom Name"
        assert business.slug == "custom"
