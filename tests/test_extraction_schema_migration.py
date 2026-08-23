import sqlite3
import pytest
import os
from decimal import Decimal
from datetime import datetime, timezone
from sqlalchemy import create_engine
from app.database.base import Base
# Import models to ensure they are registered with Base.metadata
from app.database import models

def test_migration_preserves_data(tmp_path):
    # Setup initial schema exactly as it was before migration
    db_path = tmp_path / "test_blueprint.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Minimal schema to test migration
    cursor.execute("""
        CREATE TABLE "order" (
            id INTEGER NOT NULL PRIMARY KEY,
            business_id INTEGER NOT NULL,
            status VARCHAR(50) NOT NULL,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE order_item (
            id INTEGER NOT NULL PRIMARY KEY,
            order_id INTEGER NOT NULL,
            product_name VARCHAR(255) NOT NULL,
            quantity NUMERIC(12, 3) NOT NULL,
            unit_price NUMERIC(12, 2) NOT NULL,
            line_total NUMERIC(12, 2) NOT NULL,
            created_at DATETIME NOT NULL,
            FOREIGN KEY(order_id) REFERENCES "order" (id)
        )
    """)
    
    now = datetime.now(timezone.utc).isoformat()
    cursor.execute("INSERT INTO \"order\" (id, business_id, status, created_at, updated_at) VALUES (1, 1, 'confirmed', ?, ?)", (now, now))
    cursor.execute("INSERT INTO order_item (id, order_id, product_name, quantity, unit_price, line_total, created_at) VALUES (1, 1, 'Cake', 2.0, 10.0, 20.0, ?)", (now,))
    conn.commit()
    conn.close()

    # We dynamically modify the path in our script to use this test db
    import backend.scripts.migrate_extraction_schema as migration_script
    
    # Override paths
    original_db_path = migration_script.DB_PATH
    original_backup_path = migration_script.BACKUP_PATH
    migration_script.DB_PATH = str(db_path)
    migration_script.BACKUP_PATH = str(tmp_path / "backup.db")
    
    try:
        # Run migration
        migration_script.migrate()
        
        # Verify schema is now nullable
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(order_item)")
        columns = cursor.fetchall()
        
        unit_price_col = next(c for c in columns if c[1] == 'unit_price')
        assert unit_price_col[3] == 0  # notnull flag is 0
        
        line_total_col = next(c for c in columns if c[1] == 'line_total')
        assert line_total_col[3] == 0  # notnull flag is 0
        
        # Verify data is preserved
        cursor.execute("SELECT id, product_name, unit_price, line_total FROM order_item")
        rows = cursor.fetchall()
        assert len(rows) == 1
        assert rows[0] == (1, 'Cake', 10.0, 20.0)
        
        # Verify extraction_target was created
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='extraction_target'")
        assert cursor.fetchone() is not None
        
        # Run again to test idempotency
        migration_script.migrate()
        
        cursor.execute("SELECT COUNT(*) FROM order_item")
        assert cursor.fetchone()[0] == 1
        
        conn.close()
    finally:
        migration_script.DB_PATH = original_db_path
        migration_script.BACKUP_PATH = original_backup_path

def test_new_database_gets_correct_schema(tmp_path):
    db_path = tmp_path / "new_blueprint.db"
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(bind=engine)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA table_info(order_item)")
    columns = cursor.fetchall()
    
    unit_price_col = next(c for c in columns if c[1] == 'unit_price')
    assert unit_price_col[3] == 0  # notnull flag is 0
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='extraction_target'")
    assert cursor.fetchone() is not None
    conn.close()
