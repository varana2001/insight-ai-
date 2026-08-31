"""
sql_generator.py
-----------------
Step 8: generate_sql() now optionally accepts feedback from a previous failed
attempt (the bad SQL + the error it caused), so it can be told what went
wrong and try again. The retry loop itself lives in app.py, not here — this
file's only job is still "given a question (and optional error context),
produce SQL."
"""

import os
from google import genai
from dotenv import load_dotenv

from schema_reader import get_schema_description

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MODEL_NAME = "gemini-3.6-flash"


def generate_sql(question: str, previous_sql: str = None, previous_error: str = None) -> str:
    """
    Sends the question + live schema to Gemini and returns raw SQL.

    If previous_sql and previous_error are provided, includes them in the
    prompt so Gemini can see exactly what it tried and why it failed,
    instead of guessing blind on a retry.
    """
    schema = get_schema_description()

    correction_block = ""
    if previous_sql and previous_error:
        correction_block = f"""
Your previous attempt failed. Fix it based on the error below.

Previous SQL:
{previous_sql}

Error it caused:
{previous_error}
"""

    prompt = f"""You are an expert SQL analyst.
You write SQLite SELECT queries only, based on this schema:

{schema}

Rules:
- Only write SELECT statements. Never write DDL or DML.
- Only use tables and columns that appear in the schema above.
- Return ONLY the SQL query. No explanation, no markdown code fences, no commentary.
{correction_block}
Question: {question}
"""
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
    )
    sql = response.text.strip()
    sql = sql.replace("```sql", "").replace("```", "").strip()
    return sql


if __name__ == "__main__":
    test_question = "What were the top 5 products by total sales?"
    print(generate_sql(test_question))