"""Load data/raw_transactions.csv into the transactions table (SQLite)."""
import csv
from typing import Optional

from .database import Database
from .paths import data_path


def sync_raw_transactions_csv(db: Optional[Database] = None) -> int:
    """
    Upsert rows from raw_transactions.csv using INSERT OR IGNORE per transaction_id.
    Returns number of rows processed (not necessarily newly inserted).
    """
    path = data_path("raw_transactions.csv")
    if not path.exists():
        return 0
    db = db or Database()
    n = 0
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw_cid = row.get("customer_id")
            if raw_cid is None or not str(raw_cid).strip() or str(raw_cid).strip().lower() == "nan":
                cid = None
            else:
                cid = str(raw_cid).strip()
            try:
                amt = float(row["amount"])
            except (TypeError, ValueError, KeyError):
                continue
            tid = str(row.get("transaction_id", "")).strip()
            if not tid:
                continue
            db.insert_transaction({
                "transaction_id": tid,
                "customer_id": cid,
                "amount": amt,
                "merchant_name": str(row.get("merchant_name") or ""),
                "location": str(row.get("location") or ""),
                "date_time": str(row.get("date_time") or ""),
            })
            n += 1
    return n
