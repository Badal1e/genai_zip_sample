import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import random
import csv
import numpy as np
from datetime import datetime, timedelta

from src.database import Database
from src.paths import data_path

MERCHANTS = ["Amazon", "Flipkart", "Swiggy", "Zomato", "Uber", "Netflix", None, ""]
LOCATIONS = ["Delhi", "Mumbai", "Bangalore", "Chennai", "Pune", None, ""]

db = Database()
db.initialize()


def generate_corrupted_amount():
    """
    Create messy / noisy amount values:
    - Missing values
    - Outliers
    - Wrong formats
    - Random noise
    """
    r = random.random()

    # 5% missing
    if r < 0.05:
        return None

    # 5% corrupted strings
    if r < 0.10:
        return random.choice(["ERR", "NaN", "###", "??", "invalid"])

    # 10% extremely large outliers
    if r < 0.20:
        return round(random.uniform(30000, 80000), 2)

    # Normal range but noisy
    base = random.uniform(100, 25000)
    noise = np.random.normal(0, 2500)  # heavy random noise
    return round(max(0, base + noise), 2)


def generate_transaction():
    return {
        "transaction_id": f"TXN{random.randint(100000, 999999)}",

        # Missing / corrupted customer_ids added intentionally
        "customer_id": random.choice([
            f"CUST{random.randint(1000, 9999)}",
            None,
            "",
            f"CUSTX{random.randint(100, 999)}"
        ]),

        "amount": generate_corrupted_amount(),

        "merchant_name": random.choice(MERCHANTS),

        "location": random.choice(LOCATIONS),

        # Some invalid dates
        "date_time": random.choice([
            datetime.now().isoformat(),
            "",
            None,
            "INVALID_DATE"
        ])
    }


def generate_dataset(n=1000):
    csv_path = data_path("raw_transactions.csv")
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    with open(csv_path, "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=[
            "transaction_id",
            "customer_id",
            "amount",
            "merchant_name",
            "location",
            "date_time"
        ])
        writer.writeheader()

        for _ in range(n):
            txn = generate_transaction()

            writer.writerow(txn)
            db.insert_transaction(txn)


if __name__ == "__main__":
    generate_dataset(1000)
    print("✅ Messy Dataset + DB created successfully")
