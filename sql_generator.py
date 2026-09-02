"""
sql_generator.py
-----------------
Includes retry-with-exponential-backoff for transient provider outages
(503 ServerError), separate from the self-correction loop in graph.py which
handles bad SQL, not provider downtime.
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
    """Wraps the actual API call with exponential backoff on transient
    server errors (503). Re-raises after max_retries so the caller can
    decide how to handle a persistent outage."""
    last_error = None
    for attempt in range(max_retries):
        try:
            return client.models.generate_content(model=MODEL_NAME, contents=prompt)
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
above, use the history to resolve what it's referring to.
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