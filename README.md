# InsightAI — AI-Powered Business Data Analyst

Progress: **Steps 1–10 complete** 
## What's here right now
- `data/` — synthetic e-commerce CSVs (customers, products, orders, returns)
  with realistic patterns: a February 2026 revenue dip (~50% drop, driven by
  Electronics), West region outperforming others, higher return rates on Electronics.
- `database/insight_ai.db` — SQLite database built from those CSVs
- `generate_data.py` — regenerates the CSVs if you ever want fresh/different data
- `database/create_database.py` — loads CSVs into SQLite (safe to re-run, rebuilds from scratch each time)
- `test_query.py` — proves the Python → SQLite → Pandas pipeline works

- **Step 4**: A Streamlit UI with hardcoded buttons for these same queries — no AI yet
- **Step 5**: Add Gemini (or Claude) to convert natural-language questions into SQL
- **Step 6**: Auto-extract the schema instead of hardcoding it in the prompt
- **Step 7**: SQL validation (SELECT-only)
- **Step 8**: Self-correction loop when generated SQL fails
- **Step 9**: Auto-generated charts (Plotly)
- **Step 10**: AI business explanation of results
## How to run this on your machine (VS Code)

1. Open the `insight-ai` folder in VS Code (`File > Open Folder`)
2. Open a terminal in VS Code (`` Ctrl+` `` or `View > Terminal`)
3. Create a virtual environment:
   ```bash
   python -m venv venv
   ```
4. Activate it:
   - Windows: `venv\Scripts\activate`
   - Mac/Linux: `source venv/bin/activate`
5. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
6. The data and database are already generated for you (in `data/` and `database/`).
   If you ever want to regenerate them:
   ```bash
   python generate_data.py
   python database/create_database.py
   ```
7. Run the test query:
   ```bash
   python test_query.py
   ```

You should see revenue by region and a monthly revenue table where February 2026
is noticeably lower than every other month.

## Try writing your own queries
Open `test_query.py`, change the SQL, and re-run it. Try:
- Top 5 products by revenue
- Which category has the highest return rate
- Revenue by customer age group

This is the "learn the database using normal Python first" step — get comfortable
here before Step 4 adds a UI and Step 5 adds the AI.

## What's next (don't build these yet)

- **Later**: LangGraph, conversation memory, testing, GitHub, free deployment
