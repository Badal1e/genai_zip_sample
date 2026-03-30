from src.llm_orchestrator import LLMOrchestrator
from src.nlp_processor import NLPProcessor
from src.fraud_engine import FraudEngine
from src.database import Database

db = Database()
nlp = NLPProcessor()
fraud = FraudEngine()
llm = LLMOrchestrator()

txn = db.get_transaction("TXN123456")  # replace with real ID

complaint = "I did not authorize this payment and I don't recognize the merchant"

if txn:
    txn = dict(txn)

    nlp_out = nlp.process(complaint)
    fraud_out = fraud.predict(txn)

    result = llm.generate(txn, nlp_out, fraud_out, complaint)
    print(result)
else:
    print("Transaction not found")