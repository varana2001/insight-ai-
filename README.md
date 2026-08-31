# InsightAI — AI-Powered Business Data Analyst

Ask business questions in plain English. InsightAI converts them into
validated SQL, runs them against a real sales dataset, and returns results
as a chart, table, and plain-English business explanation.

**Live demo:** [add your Streamlit Cloud URL here]

## Example
> "Which region had the highest profit?"

Returns: generated SQL → safety-validated → executed → auto-generated chart
→ business insight in plain language.

## Features
- Natural language to SQL (Google Gemini)
- Schema auto-extracted directly from the database (no hardcoded prompts)
- SQL safety validation — blocks destructive queries (DELETE/DROP/UPDATE/etc.)
  before execution
- Self-correction loop — automatically retries and fixes failed SQL using the
  error message
- Auto-generated charts based on result shape (bar/line/table)
- AI-generated plain-English business explanations

## Tech Stack
Python, Streamlit, SQLite, Google Gemini (`google-genai`), pandas, Plotly, `uv`

## Dataset
[Superstore Sales Dataset](https://www.kaggle.com/datasets/vivek468/superstore-dataset-final) (Kaggle) — 9,994 orders across 4 regions

## Run it locally
```bash
git clone https://github.com/varana2001/insight-ai-.git
cd insight-ai-
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
cp .env.example .env   # add your own GEMINI_API_KEY
python -m streamlit run app.py
```

## Architecture
```
Question → Gemini (SQL Generator) → SQL Validator → SQLite → 
Self-correction loop on error → Chart Generator → Business Analyst (Gemini) → Streamlit UI
```