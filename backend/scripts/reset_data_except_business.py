"""Reset SQLite rowid counters on empty tables while keeping business data."""

from __future__ import annotations

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "blueprint.db"

TABLES_TO_RESET = [
    "extraction_evidence",
    "extracted_fact",
    "feedback",
    "order_item",
    "order",
    "inquiry",
    "media",
    "message",
    "participant",
    "conversation",
    "import_batch",
    "whatsapp_identity",
    "customer",
]


def main() -> None:
    conn = sqlite3.connect(DB_PATH, timeout=5)
    conn.execute("PRAGMA foreign_keys = OFF")
    cur = conn.cursor()

    for table in TABLES_TO_RESET:
        row = cur.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
            (table,),
        ).fetchone()
        if row is None:
            raise RuntimeError(f"Table not found: {table}")

        ddl = row[0]
        index_rows = cur.execute(
            """
            SELECT sql FROM sqlite_master
            WHERE type='index' AND tbl_name=? AND sql IS NOT NULL
            ORDER BY name
            """,
            (table,),
        ).fetchall()

        cur.execute(f'DROP TABLE "{table}"')
        cur.execute(ddl)
        for (index_sql,) in index_rows:
            cur.execute(index_sql)

        print(f"Recreated {table} (ID counter reset)")

    conn.commit()
    conn.execute("PRAGMA foreign_keys = ON")

    print("\nRow counts:")
    tables = [
        r[0]
        for r in cur.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """
        )
    ]
    for table in tables:
        count = cur.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
        print(f"  {table}: {count}")

    conn.close()


if __name__ == "__main__":
    main()
