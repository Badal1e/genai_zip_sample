from src.fraud_engine import FraudEngine
from src.database import Database

db = Database()
engine = FraudEngine()

txn = db.get_transaction("TXN123456")  # replace with real ID

if txn:
    result = engine.predict(dict(txn))
    print(result)
else:
    print("Transaction not found")