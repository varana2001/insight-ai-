"""
analyst.py
----------
Same retry-with-backoff protection as sql_generator.py, since this file
makes an independent API call and can hit the same transient outages.
"""

import os
import time
import pandas as pd
from google import genai
from google.genai import errors
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MODEL_NAME = "gemini-3.6-flash"


def _call_with_retry(prompt: str, max_retries: int = 4):
    last_error = None
    for attempt in range(max_retries):
        try:
            return client.models.generate_content(model=MODEL_NAME, contents=prompt)
        except errors.ServerError as e:
            last_error = e
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
    raise last_error


def explain_result(question: str, df: pd.DataFrame) -> str:
    if df.empty:
        return "The query returned no results."

    sample = df.head(20).to_string(index=False)

    prompt = f"""You are a senior business analyst. A colleague asked this question:

"{question}"

Here is the data that answers it (showing up to 20 rows):

{sample}

Write a concise 2-3 sentence business explanation of what this data shows.
Mention specific numbers where relevant. Write for a non-technical business
audience — no SQL talk, no column names, plain business language.
"""
    response = _call_with_retry(prompt)
    return response.text.strip()


if __name__ == "__main__":
    test_df = pd.DataFrame({
        "region": ["East", "West", "North", "South"],
        "total_profit": [45000, 62000, 38000, 51000],
    })
    print(explain_result("Which region had the highest profit?", test_df))