import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import pandas as pd

from src.database import Database
from src.paths import data_path

db = Database()

df = pd.read_csv(data_path("raw_transactions.csv"))

for _, row in df.iterrows():
    db.insert_transaction({
        "transaction_id": row["transaction_id"],
        "customer_id": row["customer_id"],
        "amount": row["amount"],
        "merchant_name": row["merchant_name"],
        "location": row["location"],
        "date_time": row["date_time"]
    })

print("Data inserted into database.")
