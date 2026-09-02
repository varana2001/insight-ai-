"""
graph.py
--------
LangGraph pipeline: generate -> validate -> execute -> (retry on failure) ->
explain -> save_memory -> END. Includes conversation memory (fetches recent
history before generating, saves the turn after success) and graceful
handling of AI-provider failures (outages, quota limits) so they surface as
a normal failure state instead of crashing the app.
"""

from typing import TypedDict, Optional, List, Dict, Any
import sqlite3
import pandas as pd
from langgraph.graph import StateGraph, END

from sql_generator import generate_sql
from sql_validator import is_safe_sql
from analyst import explain_result
import memory

DB_PATH = "database/insight_ai.db"


class GraphState(TypedDict):
    question: str
    conversation_context: str
    sql: Optional[str]
    previous_sql: Optional[str]
    previous_error: Optional[str]
    attempt: int
    max_attempts: int
    safe: bool
    validation_reason: str
    success: bool
    result_records: Optional[List[Dict[str, Any]]]
    result_columns: Optional[List[str]]
    explanation: Optional[str]


def run_query(sql: str) -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)
    try:
        return pd.read_sql_query(sql, conn)
    finally:
        conn.close()


def generate_node(state: GraphState) -> dict:
    try:
        sql = generate_sql(
            state["question"],
            state.get("previous_sql"),
            state.get("previous_error"),
            state.get("conversation_context", ""),
        )
        return {"sql": sql, "attempt": state["attempt"] + 1}
    except Exception as e:
        # Persistent provider outage or quota limit even after retries —
        # don't crash the whole app, surface it as a normal failure state.
        return {
            "sql": None,
            "attempt": state["max_attempts"],  # force the retry loop to stop
            "success": False,
            "previous_error": f"AI provider unavailable: {e}",
        }


def validate_node(state: GraphState) -> dict:
    if state.get("sql") is None:
        return {"safe": False, "validation_reason": "No SQL was generated."}
    safe, reason = is_safe_sql(state["sql"])
    return {"safe": safe, "validation_reason": reason}


def execute_node(state: GraphState) -> dict:
    try:
        df = run_query(state["sql"])
        return {
            "success": True,
            "result_records": df.to_dict("records"),
            "result_columns": list(df.columns),
        }
    except Exception as e:
        return {
            "success": False,
            "previous_sql": state["sql"],
            "previous_error": str(e),
        }


def explain_node(state: GraphState) -> dict:
    df = pd.DataFrame(state["result_records"], columns=state["result_columns"])
    try:
        explanation = explain_result(state["question"], df)
    except Exception as e:
        explanation = f"(Business explanation unavailable due to AI service issue: {e})"
    return {"explanation": explanation}


def save_memory_node(state: GraphState) -> dict:
    """Persists this turn so future questions can reference it."""
    df = pd.DataFrame(state["result_records"], columns=state["result_columns"])
    summary = df.head(5).to_string(index=False)
    memory.save_turn(state["question"], state["sql"], summary)
    return {}


def route_after_validate(state: GraphState) -> str:
    return "execute" if state["safe"] else "blocked"


def route_after_execute(state: GraphState) -> str:
    if state["success"]:
        return "explain"
    if state["attempt"] < state["max_attempts"]:
        return "retry"
    return "failed"


def build_graph():
    graph = StateGraph(GraphState)

    graph.add_node("generate", generate_node)
    graph.add_node("validate", validate_node)
    graph.add_node("execute", execute_node)
    graph.add_node("explain", explain_node)
    graph.add_node("save_memory", save_memory_node)

    graph.set_entry_point("generate")
    graph.add_edge("generate", "validate")

    graph.add_conditional_edges(
        "validate",
        route_after_validate,
        {"execute": "execute", "blocked": END},
    )

    graph.add_conditional_edges(
        "execute",
        route_after_execute,
        {"explain": "explain", "retry": "generate", "failed": END},
    )

    graph.add_edge("explain", "save_memory")
    graph.add_edge("save_memory", END)

    return graph.compile()


def run_pipeline(question: str, max_attempts: int = 3, use_memory: bool = True) -> GraphState:
    """Runs the full graph for a question and returns the final state."""
    graph = build_graph()
    context = memory.get_recent_context(n=3) if use_memory else ""

    initial_state: GraphState = {
        "question": question,
        "conversation_context": context,
        "sql": None,
        "previous_sql": None,
        "previous_error": None,
        "attempt": 0,
        "max_attempts": max_attempts,
        "safe": False,
        "validation_reason": "",
        "success": False,
        "result_records": None,
        "result_columns": None,
        "explanation": None,
    }
    return graph.invoke(initial_state)


if __name__ == "__main__":
    memory.clear_history()

    print("--- First question ---")
    result1 = run_pipeline("Which region had the highest profit?")
    print("SQL:", result1.get("sql"))
    print("Result:", result1.get("result_records"))
    print("Explanation:", result1.get("explanation"))

    print("\n--- Follow-up referencing the previous answer ---")
    result2 = run_pipeline("Now show me that region's sales by category")
    print("SQL:", result2.get("sql"))
    print("Result:", result2.get("result_records"))