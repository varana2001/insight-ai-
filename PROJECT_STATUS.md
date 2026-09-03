# InsightAI — Project Status & Handoff Notes

**Purpose of this file:** if you run out of credits with one AI assistant, paste this
entire file to any other AI along with "help me continue this project" and it
will have everything needed to pick up exactly where you left off.

---

## FINAL STATUS: COMPLETE

All 10 original build steps + LangGraph orchestration + persistent
conversation memory confirmed working end-to-end through the actual
Streamlit UI. Also survived and gracefully handled two real production-grade
failure modes during development: a genuine Gemini API outage (503, lasted
~90 minutes) and hitting the daily free-tier quota (429) — distinguished and
handled differently (retry with backoff vs. fail-fast with a clear message).
Predefined-questions dropdown fully working after fixing a truncated code
block. Deployment to Streamlit Cloud pending final push + live verification.

---

## Goal
Build **InsightAI**, a portfolio project for Data Analyst / AI Engineer /
Data Engineer / Business Analyst job applications. A user asks a business
question in plain English, the system generates SQL, runs it against a
real dataset, and returns results + a chart + a plain-English business
explanation, with memory across turns.

## Dataset
Real Kaggle dataset: **Superstore Sales Dataset** (vivek468/superstore-dataset-final).
Loaded as a single flat table called `orders` in SQLite (9,994 rows, 21 columns:
row_id, order_id, order_date, ship_date, ship_mode, customer_id, customer_name,
segment, country, city, state, postal_code, region, product_id, category,
sub_category, product_name, sales, quantity, discount, profit).

**Known data quirk:** `order_date` and `ship_date` are stored as TEXT in
M/D/YYYY format (e.g. "11/8/2016"), not a real date type. SQLite's
`strftime()` doesn't parse this correctly — use `LIKE` pattern matching for
filtering, or parse in pandas with `pd.to_datetime(..., format="%m/%d/%Y")`.

## Tech stack
- Python 3.12, SQLite, pandas, Streamlit, Plotly
- Google Gemini API via `google-genai` (migrated from the deprecated
  `google-generativeai` package mid-project). Model: `gemini-3.6-flash`
  (only model currently available on this account/tier)
- LangGraph for pipeline orchestration
- `python-dotenv` for API key management
- `uv` for virtual environment + package management

## Environment setup
- Virtual environment: `.venv/` (created with `uv venv`)
- **Known gotcha:** if Anaconda is installed, `which streamlit` may resolve
  to Anaconda's copy instead of `.venv`'s. Fix: run
  `python -m streamlit run app.py` instead of plain `streamlit run app.py`.
- API key stored in `.env` (gitignored), placeholder in `.env.example`
  (committed)

## Project structure

insight-ai/
├── .venv/ # gitignored
├── .env # gitignored, real API key
├── .env.example # committed, placeholder
├── .gitignore
├── requirements.txt
├── README.md
├── PROJECT_STATUS.md
├── app.py # Streamlit UI
├── graph.py # LangGraph pipeline
├── sql_generator.py # NL question -> SQL via Gemini, retry/quota handling
├── sql_validator.py # SELECT-only safety validation
├── schema_reader.py # auto-extracts schema from the DB
├── chart_generator.py # picks bar/line/table based on result shape
├── analyst.py # generates plain-English business explanations
├── memory.py # persisted conversation history (SQLite)
├── graph_diagram.png # auto-generated LangGraph architecture diagram
├── data/
│ └── superstore.csv # raw Kaggle download
└── database/
├── create_database.py # loads CSV into SQLite (standalone script)
└── insight_ai.db # SQLite database (gitignored, auto-built on deploy)


## STEPS COMPLETED

- ✅ Steps 1-10 (data, structure, SQLite, Streamlit UI, AI-generated SQL,
  auto-schema, SQL validation, self-correction, charts, business explanations)
- ✅ LangGraph conversion — replaced manual for-loop with explicit state graph
- ✅ Conversation memory — persisted in SQLite, verified via UI: "that region"
  correctly resolved across turns
- ✅ Real API failure handling — 503 outage (retry w/ backoff), 429 quota
  (fail-fast), both discovered through actual production incidents during
  development, not simulated
- ✅ Fixed a truncated code block in the "Analyze" button handler (missing
  st.dataframe/st.bar_chart calls after a copy-paste edit) — dropdown
  feature fully restored

## KEY BUGS FOUND AND FIXED (good interview material)
1. CTE false positive in SQL validator — `WITH ... SELECT` queries were
   blocked since they don't start with SELECT literally
2. Circular import in sql_generator.py from a copy-paste error
3. Anaconda/`.venv` PATH conflict causing `streamlit` command to resolve to
   the wrong Python environment
4. Deployed app had no database (gitignored .db file never built on server)
   — fixed with a defensive check-and-rebuild function
5. Truncated app.py code block silently dropped chart/table display code

## PENDING
- ⬜ Final push of README/status updates
- ⬜ Confirm Streamlit Cloud redeploy picks up all changes (LangGraph,
  memory, the Analyze button fix)
- ⬜ Full live-URL test: all 5 dropdown questions + 2-question memory test
- ⬜ Add live demo URL to README once confirmed working

## Design decisions worth remembering (for interviews)
- SQLite over Postgres/MySQL early on: avoid server setup overhead while learning
- SQL generation and execution kept in separate functions/files
- Single flat `orders` table rather than normalizing, since source data is flat
- `uv` instead of plain pip/venv
- Conversation memory in SQLite, not session state — survives refresh/redeploy,
  at the cost of no per-user isolation (no auth system)
- Distinguished retry-worthy (503) vs. non-retry-worthy (429) API failures

## If you're an AI picking this up
Ask the user which pending item to continue from. Give code in small chunks
tied to one file at a time, ask the user to run and report back before
proceeding. This project has a strong pattern of catching real bugs through
actual testing — preserve that pattern.