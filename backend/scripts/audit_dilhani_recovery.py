import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "blueprint.db"

def main() -> None:
    conn = sqlite3.connect(DB_PATH, timeout=5)
    cur = conn.cursor()

    print("Starting Dilhani recovery... (Purging Business 1 derived extraction state)")

    # The order of deletion matters due to foreign keys, but we can also just use cascade 
    # if it's set up in DB, or delete explicitly.
    # Evidence must be deleted first or along with its parents. SQLite might have ON DELETE CASCADE,
    # but we will just explicitly delete to be safe.

    tables_to_purge = [
        "extraction_evidence",
        "extracted_fact",
        "feedback",
        "order_item",
        '"order"',
        "inquiry",
        "extraction_target",
    ]

    for table in tables_to_purge:
        # extraction_evidence does not have business_id, but it links to messages which do, 
        # or we can delete where it links to inquiries/orders etc that belong to business 1.
        # Actually, if we just delete the orders, SQLite might not enforce cascading if PRAGMA foreign_keys=ON wasn't run.
        pass

    # Safest way to delete extraction_evidence for Business 1:
    cur.execute("PRAGMA foreign_keys = ON")
    
    cur.execute("""
        DELETE FROM extraction_evidence 
        WHERE order_id IN (SELECT id FROM "order" WHERE business_id = 1)
           OR inquiry_id IN (SELECT id FROM inquiry WHERE business_id = 1)
           OR feedback_id IN (SELECT id FROM feedback WHERE business_id = 1)
           OR extracted_fact_id IN (SELECT id FROM extracted_fact WHERE business_id = 1)
    """)
    print(f"Deleted {cur.rowcount} rows from extraction_evidence")

    cur.execute('DELETE FROM order_item WHERE order_id IN (SELECT id FROM "order" WHERE business_id = 1)')
    print(f"Deleted {cur.rowcount} rows from order_item")

    cur.execute('DELETE FROM "order" WHERE business_id = 1')
    print(f"Deleted {cur.rowcount} rows from order")

    cur.execute('DELETE FROM inquiry WHERE business_id = 1')
    print(f"Deleted {cur.rowcount} rows from inquiry")

    cur.execute('DELETE FROM feedback WHERE business_id = 1')
    print(f"Deleted {cur.rowcount} rows from feedback")

    cur.execute('DELETE FROM extracted_fact WHERE business_id = 1')
    print(f"Deleted {cur.rowcount} rows from extracted_fact")

    cur.execute('DELETE FROM extraction_target WHERE business_id = 1')
    print(f"Deleted {cur.rowcount} rows from extraction_target")

    conn.commit()
    conn.close()
    print("Recovery script complete.")

if __name__ == "__main__":
    main()
