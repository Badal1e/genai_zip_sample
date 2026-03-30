"""
EDA for the project datasets: bundled raw_transactions.csv and optional disputes from SQLite.
Run from repo root: python eda_analysis.py
"""
import sqlite3
import sys
from pathlib import Path
from typing import Optional

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd

from src.paths import data_path


def _load_transactions() -> pd.DataFrame:
    csv_path = data_path("raw_transactions.csv")
    if not csv_path.exists():
        print("raw_transactions.csv not found. Generate with: python -m data.generate_data")
        sys.exit(1)
    df = pd.read_csv(csv_path)
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    return df


def _load_disputes() -> Optional[pd.DataFrame]:
    dbp = data_path("disputes.sqlite")
    if not dbp.exists():
        return None
    conn = sqlite3.connect(str(dbp))
    try:
        d = pd.read_sql_query(
            "SELECT case_id, transaction_id, complaint_text, classification, fraud_score, status FROM disputes",
            conn,
        )
        return d
    finally:
        conn.close()


def main():
    df = _load_transactions()
    print("=== Transactions (raw_transactions.csv) ===")
    print("Shape:", df.shape)
    print("\nDtypes:\n", df.dtypes)
    print("\nMissing values (transactions):\n", df.isnull().sum())
    print("\nAmount describe:\n", df["amount"].describe())

    amt = df["amount"].dropna()
    if len(amt) > 1:
        print("\nAmount correlation with row order (sanity):", np.corrcoef(np.arange(len(amt)), amt.values)[0, 1])

    print("\n--- Merchant distribution (top 10) ---")
    print(df["merchant_name"].value_counts(dropna=False).head(10))

    print("\n--- Location distribution ---")
    print(df["location"].value_counts(dropna=False).head(15))

    disp = _load_disputes()
    if disp is not None and not disp.empty:
        print("\n=== Disputes (SQLite) ===")
        print("Shape:", disp.shape)
        print("\nMissing values (disputes):\n", disp.isnull().sum())
        print("\nStatus counts:\n", disp["status"].value_counts(dropna=False))
        if "classification" in disp.columns:
            print("\nDispute type (NLP classification) distribution:\n")
            print(disp["classification"].value_counts(dropna=False).head(20))
        if "fraud_score" in disp.columns:
            fs = pd.to_numeric(disp["fraud_score"], errors="coerce")
            print("\nFraud score (stored) describe:\n", fs.describe())
        if "complaint_text" in disp.columns:
            lens = disp["complaint_text"].fillna("").str.len()
            print("\nComplaint text length (chars) describe:\n", lens.describe())
        merged = df.merge(disp, on="transaction_id", how="inner", suffixes=("_txn", "_disp"))
        if not merged.empty and "amount" in merged.columns and "fraud_score" in merged.columns:
            m = merged[["amount", "fraud_score"]].apply(pd.to_numeric, errors="coerce").dropna()
            if len(m) > 1:
                print(
                    "\nCorrelation amount vs fraud_score (joined rows):",
                    m["amount"].corr(m["fraud_score"]),
                )
    else:
        print("\n(No disputes.sqlite or empty disputes table — run the app and file cases for dispute-level EDA.)")

    print("\n--- Fraud / risk patterns (heuristic notes) ---")
    high_amt = (df["amount"] > 10000).sum()
    print(f"Transactions with amount > 10000: {high_amt} ({100 * high_amt / max(len(df), 1):.1f}%)")
    miss_amt = df["amount"].isna().sum()
    print(f"Missing amount values: {miss_amt}")


if __name__ == "__main__":
    main()
