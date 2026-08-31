"""
sql_validator.py
-----------------
Step 7: Before any AI-generated SQL touches the real database, check it's
safe to run.

Two checks:
1. The query must actually start with SELECT (not just "mention" it somewhere).
2. None of the dangerous keywords (DELETE, DROP, UPDATE, INSERT, ALTER,
   TRUNCATE) appear anywhere in the query — even inside a SELECT, since a
   subquery or semicolon-separated second statement could still cause damage.

This is intentionally simple (string-based) rather than a full SQL parser —
good enough to stop an LLM from doing anything destructive, and easy to
explain line-by-line in an interview. A more robust version (using a real
SQL parser like sqlglot) is a documented future improvement, not a must-have
right now.
"""

FORBIDDEN_KEYWORDS = [
    "delete", "drop", "update", "insert", "alter", "truncate", "grant", "create"
]


class SQLValidationError(Exception):
    """Raised when generated SQL fails the safety check."""
    pass


def is_safe_sql(sql: str) -> tuple[bool, str]:
    """
    Returns (True, "") if the SQL is safe to run.
    Returns (False, reason) if it's rejected.
    """
    cleaned = sql.strip().lower()

        # CTEs (WITH ... AS (...) SELECT ...) are legitimate read-only queries
    # that don't start with SELECT literally, so allow that prefix too.
    if not (cleaned.startswith("select") or cleaned.startswith("with")):
        return False, f"Query does not start with SELECT or WITH. Rejected."

    for word in FORBIDDEN_KEYWORDS:
        if f" {word} " in f" {cleaned} " or cleaned.startswith(f"{word} "):
            return False, f"Forbidden keyword detected: '{word}'. Rejected."

    return True, ""


def validate_or_raise(sql: str) -> None:
    """Same check, but raises an exception instead of returning a tuple —
    convenient when you want the caller to handle it with try/except."""
    safe, reason = is_safe_sql(sql)
    if not safe:
        raise SQLValidationError(reason)


if __name__ == "__main__":
    tests = [
        "SELECT * FROM orders WHERE region = 'West'",
        "DELETE FROM orders",
        "SELECT * FROM orders; DROP TABLE orders;",
        "select product_name from orders limit 5",
    ]
    for t in tests:
        safe, reason = is_safe_sql(t)
        print(f"{'SAFE' if safe else 'BLOCKED'}: {t}  {('-> ' + reason) if reason else ''}")