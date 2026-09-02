"""
sql_generator.py
-----------------
Converts a natural-language question into SQL using Gemini, grounded in the
live database schema (schema_reader.py) and optional conversation history
(for resolving references like "that region").

Includes retry-with-exponential-backoff for transient provider outages
(503 ServerError), and immediate clean failure for quota errors (429
ClientError/RESOURCE_EXHAUSTED) — these are different failure modes and
need different handling: retrying a 503 can help since the server may
recover in seconds; retrying a daily quota limit never helps, so we fail
fast with a clear message instead of wasting attempts.
"""

import os
import time
from google import genai
from google.genai import errors
from dotenv import load_dotenv

from schema_reader import get_schema_description

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MODEL_NAME = "gemini-3.6-flash"


def _call_with_retry(prompt: str, max_retries: int = 4):
    """
    Wraps the actual API call.
    - ServerError (503, temporary outage): retry with exponential backoff.
    - ClientError with RESOURCE_EXHAUSTED (429, daily quota): fail immediately
      with a clear message — retrying won't help a 24-hour quota limit.
    - Any other ClientError: fail immediately too, since it's likely a real
      problem with the request itself, not something a retry would fix.
    """
    last_error = None
    for attempt in range(max_retries):
        try:
            return client.models.generate_content(model=MODEL_NAME, contents=prompt)
        except errors.ClientError as e:
            if "RESOURCE_EXHAUSTED" in str(e):
                raise RuntimeError(
                    "Daily API quota reached. Try again after the quota resets "
                    "(check ai.google.dev for reset timing)."
                ) from e
            raise
        except errors.ServerError as e:
            last_error = e
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # 1s, 2s, 4s, 8s
    raise last_error


def generate_sql(
    question: str,
    previous_sql: str = None,
    previous_error: str = None,
    conversation_context: str = "",
) -> str:
    """
    Sends the question + live schema (+ optional error-correction context +
    optional recent conversation history) to Gemini and returns raw SQL.
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

    context_block = ""
    if conversation_context:
        context_block = f"""
{conversation_context}

If the current question references something from the conversation history
above (e.g. "that region", "the same period", "now break it down by X"),
use the history to resolve what it's referring to.
"""

    prompt = f"""You are an expert SQL analyst.
You write SQLite SELECT queries only, based on this schema:

{schema}
{context_block}
Rules:
- Only write SELECT statements. Never write DDL or DML.
- Only use tables and columns that appear in the schema above.
- Return ONLY the SQL query. No explanation, no markdown code fences, no commentary.
{correction_block}
Question: {question}
"""
    response = _call_with_retry(prompt)
    sql = response.text.strip()
    sql = sql.replace("```sql", "").replace("```", "").strip()
    return sql


if __name__ == "__main__":
    test_question = "What were the top 5 products by total sales?"
    print(generate_sql(test_question))