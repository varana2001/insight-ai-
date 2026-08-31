"""
memory.py
---------
Conversation memory, persisted in a SQLite table (not Streamlit session
state), so it survives browser refreshes, closing the tab, and even
redeploys — since it's just rows in insight_ai.db, same as your orders data.

Design note: this app has no login/auth system, so there's no concept of
"which user" a conversation belongs to — this is a single shared history for
whoever uses the app. A multi-user version would add a user_id/session_id
column and filter by it; documented here as a known simplification, not an
oversight.
"""

import sqlite3
from datetime import datetime

DB_PATH = "database/insight_ai.db"


def ensure_memory_table() -> None:
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                sql TEXT,
                result_summary TEXT,
                created_at TEXT NOT NULL
            );
        """)
        conn.commit()
    finally:
        conn.close()


def save_turn(question: str, sql: str, result_summary: str) -> None:
    """Persists one Q&A turn so future questions can reference it."""
    ensure_memory_table()
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            "INSERT INTO conversation_history (question, sql, result_summary, created_at) "
            "VALUES (?, ?, ?, ?)",
            (question, sql, result_summary, datetime.now().isoformat()),
        )
        conn.commit()
    finally:
        conn.close()


def get_recent_context(n: int = 3) -> str:
    """
    Returns the last n turns formatted as plain text, for injection into the
    SQL generation prompt. Empty string if there's no history yet.
    """
    ensure_memory_table()
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.execute(
            "SELECT question, sql, result_summary FROM conversation_history "
            "ORDER BY id DESC LIMIT ?",
            (n,),
        )
        rows = cur.fetchall()
    finally:
        conn.close()

    if not rows:
        return ""

    rows.reverse()  # oldest first, so it reads chronologically
    lines = ["Recent conversation history (most recent question last):"]
    for question, sql, summary in rows:
        lines.append(f'- Previous question: "{question}"')
        lines.append(f"  SQL used: {sql}")
        if summary:
            lines.append(f"  Result: {summary}")
    return "\n".join(lines)


def clear_history() -> None:
    ensure_memory_table()
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("DELETE FROM conversation_history")
        conn.commit()
    finally:
        conn.close()


def get_all_history() -> list[tuple]:
    """For displaying history in the UI, if wanted."""
    ensure_memory_table()
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.execute(
            "SELECT question, sql, created_at FROM conversation_history ORDER BY id DESC"
        )
        return cur.fetchall()
    finally:
        conn.close()


if __name__ == "__main__":
    clear_history()
    save_turn(
        "Which region had the highest profit?",
        "SELECT region FROM orders GROUP BY region ORDER BY SUM(profit) DESC LIMIT 1",
        "West",
    )
    print(get_recent_context())