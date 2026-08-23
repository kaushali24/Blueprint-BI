import os
import shutil
import sqlite3
import sys

# Add the backend directory to Python path so we can import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine
from app.database.base import Base
# We import models so that Base.metadata has all tables registered
from app.database import models

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'blueprint.db'))
BACKUP_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'blueprint_before_extraction_migration.db'))

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}. Exiting.")
        return

    # Backup
    if not os.path.exists(BACKUP_PATH):
        print(f"Creating backup at {BACKUP_PATH}...")
        shutil.copy2(DB_PATH, BACKUP_PATH)
    else:
        print(f"Backup already exists at {BACKUP_PATH}.")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check idempotency
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='order_item'")
    row = cursor.fetchone()
    if not row:
        print("order_item table does not exist. Exiting.")
        return

    sql = row[0]
    if "unit_price NUMERIC(12, 2) NOT NULL" not in sql and "unit_price" in sql and "NOT NULL" not in sql.split("unit_price")[1].split(",")[0]:
        print("unit_price is already nullable. Checking if we need to run create_all().")
        # Still run create_all to ensure ExtractionTarget exists if someone ran migration partially
        engine = create_engine(f"sqlite:///{DB_PATH}")
        Base.metadata.create_all(bind=engine)
        print("Migration already applied. Exiting idempotently.")
        return
        
    # We will look for NOT NULL in unit_price
    # Since SQLite's exact DDL string can vary, a safe check is to just read the table_info
    cursor.execute("PRAGMA table_info(order_item)")
    columns = cursor.fetchall()
    unit_price_col = next((c for c in columns if c[1] == 'unit_price'), None)
    
    if unit_price_col and not unit_price_col[3]:  # c[3] is 'notnull' flag
        print("unit_price is already nullable (via PRAGMA check). Exiting idempotently.")
        engine = create_engine(f"sqlite:///{DB_PATH}")
        Base.metadata.create_all(bind=engine)
        return

    print("Migrating order_item schema to make unit_price and line_total nullable...")

    cursor.execute("BEGIN TRANSACTION")
    try:
        # Create new table
        cursor.execute("""
            CREATE TABLE order_item_new (
                id INTEGER NOT NULL PRIMARY KEY,
                order_id INTEGER NOT NULL,
                product_name VARCHAR(255) NOT NULL,
                quantity NUMERIC(12, 3) NOT NULL,
                unit_price NUMERIC(12, 2),
                line_total NUMERIC(12, 2),
                created_at DATETIME NOT NULL,
                FOREIGN KEY(order_id) REFERENCES "order" (id)
            )
        """)

        # Copy data
        cursor.execute("""
            INSERT INTO order_item_new (id, order_id, product_name, quantity, unit_price, line_total, created_at)
            SELECT id, order_id, product_name, quantity, unit_price, line_total, created_at
            FROM order_item
        """)

        # Verify row counts
        cursor.execute("SELECT COUNT(*) FROM order_item")
        old_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM order_item_new")
        new_count = cursor.fetchone()[0]

        if old_count != new_count:
            raise Exception(f"Row count mismatch! Old: {old_count}, New: {new_count}")

        # Drop old and rename new
        cursor.execute("DROP TABLE order_item")
        cursor.execute("ALTER TABLE order_item_new RENAME TO order_item")

        # Re-create index
        cursor.execute("CREATE INDEX ix_order_item_order_id ON order_item (order_id)")

        conn.commit()
        print(f"Successfully migrated order_item. Preserved {new_count} rows.")

    except Exception as e:
        conn.rollback()
        print(f"Migration failed: {e}")
        raise
    finally:
        conn.close()

    # Run create_all to create extraction_target table
    print("Running Base.metadata.create_all() to ensure ExtractionTarget exists...")
    engine = create_engine(f"sqlite:///{DB_PATH}")
    Base.metadata.create_all(bind=engine)
    print("Database initialization complete.")

if __name__ == "__main__":
    migrate()
