from typing import Tuple

import pandas as pd

REQUIRED_TRANSACTION_COLUMNS = [
    "transaction_id",
    "customer_id",
    "amount",
    "merchant_name",
    "location",
    "date_time",
]


def validate_transaction_csv_df(df: pd.DataFrame) -> Tuple[bool, str]:
    missing = [c for c in REQUIRED_TRANSACTION_COLUMNS if c not in df.columns]
    if missing:
        return False, f"Missing columns: {', '.join(missing)}"
    if df.empty:
        return False, "CSV has no data rows."
    return True, ""
