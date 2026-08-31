"""
schema_reader.py
-----------------
Step 6: Reads the real schema directly from insight_ai.db, so sql_generator.py
never relies on a manually-typed description that can go stale.

SQLite stores schema info in two places we use here:
- sqlite_master: lists all tables
- PRAGMA table_info(table_name): lists columns + declared type for one table
"""

import sqlite3

DB_PATH = "database/insight_ai.db"

# Things the schema itself can't tell us (e.g. SQLite just says order_date is
# TEXT — it doesn't know the text is M/D/YYYY format). We keep a small,
# manually-curated set of notes like this, separate from the auto-extracted
# structure, since this is genuinely business/data knowledge, not schema.
KNOWN_DATA_QUIRKS = """
Known data quirks (not visible from schema alone):
- order_date and ship_date are stored as TEXT in M/D/YYYY format (e.g. "11/8/2016"),
  not a real date type. SQLite's strftime() will not parse this correctly.
  Use LIKE pattern matching (e.g. WHERE order_date LIKE '11/%/2016') for date filtering,
  or convert the format explicitly if date arithmetic is needed.
"""


def get_connection():
    return sqlite3.connect(DB_PATH)


def get_table_names() -> list[str]:
    """Returns all real tables, excluding SQLite's internal bookkeeping tables."""
    conn = get_connection()
    try:
        cur = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
        )
        return [row[0] for row in cur.fetchall()]
    finally:
        conn.close()


def get_schema_description() -> str:
    """
    Builds a plain-text schema description (table names + columns + types)
    by reading the database directly, plus the known data quirks above.
    This is what gets injected into the LLM prompt instead of a hardcoded string.
    """
    conn = get_connection()
    lines = []
    try:
        for table_name in get_table_names():
            lines.append(f"Table: {table_name}")
            cur = conn.execute(f"PRAGMA table_info({table_name});")
            for _, col_name, col_type, _, _, _ in cur.fetchall():
                lines.append(f"  - {col_name} ({col_type})")
    finally:
        conn.close()

    schema_text = "\n".join(lines)
    return f"{schema_text}\n\n{KNOWN_DATA_QUIRKS}"


if __name__ == "__main__":
    print(get_schema_description())