from .database import Database
from .sync_raw_csv import sync_raw_transactions_csv

if __name__ == "__main__":
    db = Database()
    db.initialize()
    n = sync_raw_transactions_csv(db)
    if n:
        print(f"Database initialized successfully. Loaded {n} rows from data/raw_transactions.csv into transactions.")
    else:
        print(
            "Database initialized successfully. "
            "(No data/raw_transactions.csv or file empty — add CSV or run: python -m data.generate_data)"
        )