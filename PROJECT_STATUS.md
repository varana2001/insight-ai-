# InsightAI — Project Status & Handoff Notes

**Purpose of this file:** if you run out of credits with one AI assistant, paste this
entire file to any other AI (ChatGPT, Claude, Gemini, another Claude session, etc.)
along with the phrase "help me continue this project" and it will have everything
needed to pick up exactly where you left off.

---

## Goal
Build **InsightAI**, a portfolio project for Data Analyst / AI Engineer / Data
Engineer / Business Analyst job applications. A user asks a business question in
plain English, the system generates SQL, runs it against a real dataset, and
returns results + (eventually) a chart + a plain-English business explanation.

## Dataset
Real Kaggle dataset: **Superstore Sales Dataset** (vivek468/superstore-dataset-final).
Loaded as a single flat table called `orders` in SQLite (9,994 rows, 21 columns:
row_id, order_id, order_date, ship_date, ship_mode, customer_id, customer_name,
segment, country, city, state, postal_code, region, product_id, category,
sub_category, product_name, sales, quantity, discount, profit).

**Known data quirk:** `order_date` and `ship_date` are stored as TEXT in M/D/YYYY
format (e.g. "11/8/2016"), NOT a real date type. SQLite's `strftime()` doesn't
parse this correctly — either use `LIKE` pattern matching for filtering, or parse
in pandas with `pd.to_datetime(df["order_date"], format="%m/%d/%Y")` when doing
date-based aggregation.

## Tech stack (all free tier so far)
- Python 3.12
- SQLite (built into Python, no install needed)
- pandas
- Streamlit (UI)
- Google Gemini API (`google-generativeai` package) — model currently in use:
  `gemini-3.6-flash` (Google deprecates model versions periodically — if you get
  a `404 NotFound` error mentioning a model name, check Google's current model
  list and update the model string in `sql_generator.py`)
- `python-dotenv` for API key management
- `uv` for virtual environment + package management (faster alternative to
  plain pip/venv)

## Environment setup
- Virtual environment: `.venv/` (created with `uv venv`, activated with
  `source .venv/bin/activate`)
- **Known gotcha:** if you have Anaconda installed, `which streamlit` may
  resolve to Anaconda's copy instead of `.venv`'s, causing import errors even
  when `.venv` is active. Fix: run `python -m streamlit run app.py` instead of
  plain `streamlit run app.py` — this forces it to use whichever Python is
  currently active.
- API key stored in `.env` (gitignored, never committed) as `GEMINI_API_KEY=...`
- `.env.example` has a placeholder version, safe to commit

## Project structure (current)
insight-ai/
├── .venv/ # gitignored
├── .env # gitignored, real API key
├── .env.example # committed, placeholder
├── .gitignore
├── requirements.txt
├── README.md
├── app.py # Streamlit UI
├── sql_generator.py # NL question -> SQL via Gemini
├── schema_reader.py # auto-extracts schema from the DB (Step 6)
├── data/
│ └── superstore.csv # raw Kaggle download
└── database/
├── create_database.py # loads CSV into SQLite
└── insight_ai.db # SQLite database (gitignored)


## requirements.txt (current contents)

pandas
streamlit
google-generativeai
python-dotenv

## STEPS COMPLETED

- ✅ **Step 1 — Data**: Downloaded real Superstore CSV from Kaggle, placed in `data/`
- ✅ **Step 2 — Project structure**: folders set up as above
- ✅ **Step 3 — Python ↔ SQLite**: `create_database.py` loads the CSV into
  SQLite with encoding fallback (utf-8 → cp1252 → latin1) and cleaned column
  names (lowercase, underscores). Verified working, 9,994 rows loaded.
- ✅ **Step 4 — Streamlit UI (hardcoded questions)**: dropdown with 5 predefined
  business questions (top products, profit by region, monthly trend, top
  customers, sales by category), each running hardcoded SQL and showing a
  chart. Verified working.
- ✅ **Step 5 — AI-generated SQL**: added a natural-language text box above the
  dropdown. User types a question, Gemini generates SQL (schema was hardcoded
  in the prompt at this stage), SQL executes, results display. Verified
  working — tested with several real questions and confirmed:
  - Gemini correctly interprets ambiguous business language (e.g.
    "best-selling item" → correctly used `SUM(quantity)`, not sales/profit)
  - Gemini respects schema notes given in the prompt (used `LIKE` pattern for
    date filtering instead of broken `strftime()`)
  - **Important finding**: Gemini does NOT reliably refuse dangerous-sounding
    requests. Asked "delete all orders from the West region" — it did not
    write a DELETE, but silently reframed it into
    `SELECT * FROM orders WHERE region != 'West'`, which could be misleading
    if a user assumed data was actually deleted. This is the motivating
    example for why Step 7 (code-level validation) is necessary — an LLM's
    own judgment about what's "safe" is not reliable enough on its own.
- 🔄 **Step 6 — Auto-extract schema (IN PROGRESS)**: `schema_reader.py`
  created, reads schema live from `insight_ai.db` via `sqlite_master` and
  `PRAGMA table_info()`, includes a manually-curated note about the date
  format quirk (since that's business/data knowledge the schema itself can't
  reveal). `sql_generator.py` updated to import and use this instead of a
  hardcoded schema string. **Status: code written, needs to be verified
  running** — confirm `python schema_reader.py` prints correct output, then
  confirm the Streamlit app still generates correct SQL using the new dynamic
  schema.
✅ Step 7 (SQL validation) confirmed working — blocks DELETE/DROP/etc.
   Tested repeatedly with "delete all orders from West" — Gemini never
   generates an actual DELETE, it reframes into different SELECT variants
   each time (once excluding West, once filtering to only West). Validator
   correctly passes these since they ARE safe SELECTs — but this reveals a
   separate risk: the AI can silently change the meaning of a request rather
   than either doing it or refusing it. Not something the validator is meant
   to catch (it's not unsafe SQL), but worth noting as a UX/trust concern.

- ⬜ **Step 8 — Self-correction loop**: if generated SQL fails (wrong
  table/column, syntax error), send the error back to Gemini and let it retry,
  instead of showing the raw error to the user.
  - ⬜ **Step 9 — Auto-generated charts**: currently the Step 4 hardcoded
  questions have manual chart calls (`st.bar_chart`, `st.line_chart`); the
  Step 5 AI section does not yet auto-pick a chart type based on result shape.

- ⬜ **Step 10 — AI business explanation**: turn the raw query result into a
  2-3 sentence plain-English business explanation (separate LLM call).

## STEPS NOT YET STARTED

- ⬜ **LangGraph**: convert the linear pipeline into an actual graph with
  conditional routing (safe/unsafe SQL) and the self-correction loop as a
  graph edge instead of a for-loop.
- ⬜ **Conversation memory**: resolving references like "compare this month to
  last month" across turns. Not started.
- ⬜ **Testing**: no pytest tests written yet.
- ⬜ **GitHub**: project not yet pushed to a repo (`.gitignore` is ready for
  this though).
- ⬜ **Deployment**: Streamlit Community Cloud deployment not yet done.

## Design decisions worth remembering (for interviews)
- Chose SQLite over Postgres/MySQL for the early build to avoid server setup
  overhead while learning — deliberate, not a limitation.
- Kept SQL generation (`sql_generator.py`) and SQL execution (`app.py`)
  in separate files/functions from the start, per good practice: an LLM
  module should never execute what it generates.
- Chose a single flat `orders` table rather than immediately normalizing into
  customers/products tables, since Superstore ships as one flat file and
  premature normalization wasn't worth the complexity at this stage. Can
  revisit normalization later as an explicit improvement.
- Used `uv` instead of plain pip/venv for faster, isolated environment
  management.

## If you're an AI picking this up
Ask the user which step they want to continue from (likely Step 6 verification
or Step 7). Don't jump ahead — this project is being built incrementally and
deliberately, one small piece at a time, with the user running and verifying
each piece themselves before moving on. Give code in small chunks tied to one
file at a time, not large multi-file dumps, and ask the user to run and report
back before proceeding.