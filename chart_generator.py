"""
chart_generator.py
-------------------
Step 9: Looks at the shape of a query result and picks an appropriate chart
type automatically, instead of the user (or you, in code) deciding manually
every time.

Simple heuristic, easy to explain in an interview:
- A column whose name suggests time (year/month/date) + one numeric column
  -> line chart (trend over time)
- Exactly one categorical column + one numeric column -> bar chart
  (comparison across categories)
- Anything else (too many columns, no numeric column, single value, etc.)
  -> no chart, just show the table
"""

import plotly.express as px
import pandas as pd

TIME_KEYWORDS = ["year", "month", "date", "quarter"]


def pick_chart(df: pd.DataFrame):
    """
    Returns a Plotly figure, or None if a chart doesn't make sense for this
    result (caller should just show the table in that case).
    """
    if df.empty or len(df.columns) < 2:
        return None

    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    non_numeric_cols = [c for c in df.columns if c not in numeric_cols]

    if not numeric_cols:
        return None  # nothing to plot on the y-axis

    # Does any non-numeric column look like a time axis?
    time_col = next(
        (c for c in non_numeric_cols if any(kw in c.lower() for kw in TIME_KEYWORDS)),
        None,
    )

    if time_col:
        return px.line(
            df, x=time_col, y=numeric_cols[0],
            title=f"{numeric_cols[0]} by {time_col}",
            markers=True,
        )

    # One categorical + one numeric column -> bar chart
    if len(non_numeric_cols) == 1 and len(numeric_cols) >= 1:
        return px.bar(
            df, x=non_numeric_cols[0], y=numeric_cols[0],
            title=f"{numeric_cols[0]} by {non_numeric_cols[0]}",
        )

    # Anything more complex (many columns, multiple categories) -> let the
    # user read the table rather than guess at a misleading chart
    return None


if __name__ == "__main__":
    # quick manual test with fake data shaped like real query results
    test_df1 = pd.DataFrame({"region": ["East", "West", "South"], "total_sales": [100, 300, 150]})
    test_df2 = pd.DataFrame({"year": ["2016", "2017", "2018"], "total_sales": [100, 300, 150]})
    test_df3 = pd.DataFrame({"a": [1], "b": [2], "c": [3], "d": [4]})

    print("Bar chart case:", pick_chart(test_df1) is not None)
    print("Line chart case:", pick_chart(test_df2) is not None)
    print("No chart case:", pick_chart(test_df3) is None)