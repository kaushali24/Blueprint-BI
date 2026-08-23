import sqlite3
import os
import sys

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'blueprint.db')

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        print("Starting extraction consolidation migration...")
        
        # 1. Drop the legacy extraction_target table
        cursor.execute("DROP TABLE IF EXISTS extraction_target")
        print("Dropped legacy extraction_target table.")

        # 2. Recreate extraction_target with new schema
        cursor.execute("""
            CREATE TABLE extraction_target (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                business_id INTEGER NOT NULL,
                conversation_id INTEGER NOT NULL,
                start_message_id INTEGER NOT NULL,
                end_message_id INTEGER NOT NULL,
                status VARCHAR(50) NOT NULL DEFAULT 'pending',
                attempted_at DATETIME,
                completed_at DATETIME,
                failure_reason TEXT,
                created_at DATETIME NOT NULL,
                FOREIGN KEY(business_id) REFERENCES business(id),
                FOREIGN KEY(conversation_id) REFERENCES conversation(id),
                FOREIGN KEY(start_message_id) REFERENCES message(id),
                FOREIGN KEY(end_message_id) REFERENCES message(id),
                CONSTRAINT uq_extraction_target_business_conv_start UNIQUE (business_id, conversation_id, start_message_id)
            )
        """)
        print("Created new extraction_target table.")

        # 3. Helper to add extraction_target_id column if it doesn't exist
        def add_column_if_not_exists(table_name, column_def):
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [col[1] for col in cursor.fetchall()]
            if 'extraction_target_id' not in columns:
                cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN extraction_target_id INTEGER REFERENCES extraction_target(id)")
                print(f"Added extraction_target_id to {table_name}.")
            else:
                print(f"Column extraction_target_id already exists in {table_name}.")

        add_column_if_not_exists('inquiry', 'INTEGER REFERENCES extraction_target(id)')
        add_column_if_not_exists('"order"', 'INTEGER REFERENCES extraction_target(id)')
        add_column_if_not_exists('feedback', 'INTEGER REFERENCES extraction_target(id)')
        add_column_if_not_exists('extracted_fact', 'INTEGER REFERENCES extraction_target(id)')
        
        # Note: OrderItem cascades from Order, but if we need it explicitly we could add it.
        # The design says Order, Inquiry, Feedback, ExtractedFact.

        conn.commit()
        print("Migration completed successfully.")

    except Exception as e:
        conn.rollback()
        print(f"Migration failed: {e}")
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
