"""
sql_generator.py
-----------------
Now accepts optional conversation_context, so references like "that region"
or "now break it down by month" can be resolved using recent conversation
history rather than treating every question as fully independent.
"""

import os
from google import genai
from dotenv import load_dotenv

from schema_reader import get_schema_description

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MODEL_NAME = "gemini-2.5-flash"


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