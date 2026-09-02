"""
app.py
------
Step 4 (hardcoded questions) + Step 5 (AI-generated SQL) side by side,
so you can compare the AI's output against your own known-correct queries.
"""

import sqlite3
import pandas as pd
import streamlit as st
from chart_generator import pick_chart
from graph import run_pipeline
import os
import memory

DB_PATH = "database/insight_ai.db"

import os

def ensure_database_exists():
    """Build the database from the CSV if it's missing OR if it exists but
    is empty/broken (e.g. leftover from an earlier failed deploy)."""
    needs_rebuild = True

    if os.path.exists(DB_PATH):
        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='orders';"
            )
            if cur.fetchone() is not None:
                needs_rebuild = False
            conn.close()
        except Exception:
            needs_rebuild = True

    if not needs_rebuild:
        return

    csv_path = "data/superstore.csv"
    df = None
    for encoding in ["utf-8", "cp1252", "latin1"]:
        try:
            df = pd.read_csv(csv_path, encoding=encoding)
            break
        except UnicodeDecodeError:
            continue

    if df is None:
        raise RuntimeError("Could not read the CSV with any common encoding.")

    df.columns = [c.strip().lower().replace(" ", "_").replace("-", "_") for c in df.columns]

    os.makedirs("database", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        df.to_sql("orders", conn, if_exists="replace", index=False)
        conn.commit()
    finally:
        conn.close()

ensure_database_exists()




def run_query(sql: str) -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query(sql, conn)
    finally:
        conn.close()
    return df

st.set_page_config(page_title="InsightAI", layout="wide")
st.title("InsightAI")
st.caption("AI-Powered Business Data Analyst")

if st.sidebar.button("Clear conversation memory"):
    memory.clear_history()
    st.sidebar.success("Conversation history cleared")

# ---------- STEP 5: Ask in natural language ----------
st.header("Ask a question (AI-generated SQL)")
nl_question = st.text_input(
    "Ask a business question",
    placeholder="Which region had the highest profit?",
)

if st.button("Ask AI") and nl_question:
    if result.get("sql") is None:
        st.error(f"⚠️ AI service is currently unavailable. {result.get('previous_error', '')} Please try again in a few minutes.")
    elif result.get("sql"):
        ...  # rest of your existing display logic
    with st.spinner("Running pipeline..."):
        result = run_pipeline(nl_question)

    if result.get("sql"):
        st.subheader("Generated SQL")
        st.code(result["sql"], language="sql")

    if not result.get("safe", True) and not result.get("success"):
        st.error(f"🛑 Query blocked by safety validator: {result.get('validation_reason')}")
    elif result.get("success"):
        st.success("✅ Passed safety validation and executed successfully")

        df = pd.DataFrame(result["result_records"], columns=result["result_columns"])

        st.subheader("Business Insight")
        st.write(result.get("explanation"))

        chart = pick_chart(df)
        if chart is not None:
            st.plotly_chart(chart, use_container_width=True)

        st.subheader("Result")
        st.dataframe(df)
    else:
        st.error(f"Could not generate working SQL after {result.get('attempt')} attempts. Last error: {result.get('previous_error')}")

# ---------- STEP 4: Predefined questions (kept for comparison) ----------
st.header("Predefined questions (hardcoded SQL)")
question = st.selectbox(
    "Pick a business question",
    [
        "Top 5 products by total sales",
        "Profit by region",
        "Monthly sales trend",
        "Top 5 customers by total sales",
        "Sales by category",
    ],
)

if st.button("Analyze"):

    if question == "Top 5 products by total sales":
        sql = """
            SELECT product_name, ROUND(SUM(sales), 2) AS total_sales
            FROM orders
            GROUP BY product_name
            ORDER BY total_sales DESC
            LIMIT 5;
        """
        df = run_query(sql)