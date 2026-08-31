import sqlite3
import pandas as pd
import os

CSV_PATH = "data/superstore.csv"
DB_PATH = "database/insight_ai.db"


def load_csv():
    for encoding in ["utf-8", "cp1252", "latin1"]:
        try:
            df = pd.read_csv(CSV_PATH, encoding=encoding)
            print(f"Loaded with encoding='{encoding}'")
            return df
        except UnicodeDecodeError:
            print(f"encoding='{encoding}' failed, trying next...")
    raise RuntimeError("Could not read the CSV with utf-8, cp1252, or latin1.")


def clean_column_names(df):
    df.columns = [c.strip().lower().replace(" ", "_").replace("-", "_") for c in df.columns]
    return df


def main():
    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(f"Expected {CSV_PATH} — check your file is named/placed correctly.")

    df = load_csv()
    df = clean_column_names(df)

    print(f"\nShape: {df.shape[0]} rows, {df.shape[1]} columns")
    print("\nColumn names after cleaning:")
    print(list(df.columns))
    print("\nFirst 3 rows:")
    print(df.head(3).to_string())

    os.makedirs("database", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        df.to_sql("orders", conn, if_exists="replace", index=False)
        conn.commit()
    finally:
        conn.close()

    print(f"\nSaved {len(df)} rows to table 'orders' in {DB_PATH}")


if __name__ == "__main__":
    main()