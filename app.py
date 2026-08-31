"""
app.py
------
Step 4 (hardcoded questions) + Step 5 (AI-generated SQL) side by side,
so you can compare the AI's output against your own known-correct queries.
"""

import sqlite3
import pandas as pd
import streamlit as st
from sql_generator import generate_sql
from sql_validator import is_safe_sql
from chart_generator import pick_chart
from analyst import explain_result
import os
DB_PATH = "database/insight_ai.db"

def ensure_database_exists():
    """If insight_ai.db doesn't exist yet (e.g. fresh deployment where the
    .db file was gitignored), build it from the CSV automatically."""
    if os.path.exists(DB_PATH):
        return

    csv_path = "data/superstore.csv"
    for encoding in ["utf-8", "cp1252", "latin1"]:
        try:
            df = pd.read_csv(csv_path, encoding=encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
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

# ---------- STEP 5: Ask in natural language ----------
st.header("Ask a question (AI-generated SQL)")
nl_question = st.text_input(
    "Ask a business question",
    placeholder="Which region had the highest profit?",
)

if st.button("Ask AI") and nl_question:
    max_attempts = 3
    sql = None
    previous_sql = None
    previous_error = None
    df = None
    success = False

    for attempt in range(1, max_attempts + 1):
        with st.spinner(f"Generating SQL (attempt {attempt}/{max_attempts})..."):
            sql = generate_sql(nl_question, previous_sql, previous_error)

        safe, reason = is_safe_sql(sql)
        if not safe:
            st.error(f"🛑 Query blocked by safety validator: {reason}")
            break  # don't retry a safety rejection — that's not a "fix the bug" situation

        try:
            df = run_query(sql)
            success = True
            break  # got a working query, stop retrying
        except Exception as e:
            previous_sql = sql
            previous_error = str(e)
            st.warning(f"Attempt {attempt} failed: {previous_error}. Retrying..." if attempt < max_attempts else f"Attempt {attempt} failed: {previous_error}")

    st.subheader("Generated SQL")
    st.code(sql, language="sql")

    if success:
        st.success("✅ Passed safety validation and executed successfully")

        with st.spinner("Analyzing results..."):
            explanation = explain_result(nl_question, df)
        st.subheader("Business Insight")
        st.write(explanation)

        chart = pick_chart(df)
        if chart is not None:
            st.plotly_chart(chart, use_container_width=True)

        st.subheader("Result")
        st.dataframe(df)
    elif df is None and previous_error:
        st.error(f"Could not generate working SQL after {max_attempts} attempts. Last error: {previous_error}")

st.divider()

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