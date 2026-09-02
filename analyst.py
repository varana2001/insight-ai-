"""
analyst.py
----------
Step 10: Takes the raw query result and turns it into a short, plain-English
business explanation — a separate LLM call from SQL generation, since these
are genuinely different jobs (one writes SQL, the other writes prose for a
non-technical reader).
"""

import os
import pandas as pd
from google import genai
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MODEL_NAME = "gemini-2.5-flash"


def explain_result(question: str, df: pd.DataFrame) -> str:
    """Sends the question + result data to Gemini and returns a short business explanation."""
    if df.empty:
        return "The query returned no results."

    # Send at most 20 rows to keep the prompt small and cheap — the model
    # doesn't need every row to describe a trend or comparison, and this
    # keeps the response fast even on large result sets.
    sample = df.head(20).to_string(index=False)

    prompt = f"""You are a senior business analyst. A colleague asked this question:

"{question}"

Here is the data that answers it (showing up to 20 rows):

{sample}

Write a concise 2-3 sentence business explanation of what this data shows.
Mention specific numbers where relevant. Write for a non-technical business
audience — no SQL talk, no column names, plain business language.
"""
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
    )
    return response.text.strip()


if __name__ == "__main__":
    test_df = pd.DataFrame({
        "region": ["East", "West", "North", "South"],
        "total_profit": [45000, 62000, 38000, 51000],
    })
    print(explain_result("Which region had the highest profit?", test_df))