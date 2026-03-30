from typing import Any, Dict, Optional

from src.database import Database
from src.email_notify import send_complaint_registered_email
from src.ids import generate_customer_id


db = Database()


class IngestionService:
    def __init__(self):
        self.db = db

    def validate_input(self, transaction_id: str, complaint: str, customer_email: str):
        if not transaction_id or not complaint:
            raise ValueError("Missing required fields")
        if not (customer_email or "").strip():
            raise ValueError("Email is required for acknowledgement and case updates")

    def fetch_transaction(self, transaction_id: str):
        txn = self.db.get_transaction(transaction_id)
        if not txn:
            raise ValueError("Transaction not found")
        return dict(txn)

    def create_dispute(
        self,
        transaction_id: str,
        complaint: str,
        customer_email: str,
        manual_txn: Optional[Dict[str, Any]] = None,
    ):
        self.validate_input(transaction_id, complaint, customer_email)

        transaction_id = str(transaction_id).strip()
        ce = str(customer_email).strip()

        if manual_txn is not None:
            cid = generate_customer_id()
            payload = {**manual_txn, "transaction_id": transaction_id, "customer_id": cid}
            self.db.insert_transaction(payload)

        txn = self.fetch_transaction(transaction_id)
        cid = str(txn.get("customer_id") or "").strip()
        if not cid:
            cid = generate_customer_id()
            self.db.update_transaction_customer_id(transaction_id, cid)
            txn["customer_id"] = cid

        case_id = self.db.insert_dispute({
            "transaction_id": transaction_id,
            "complaint_text": complaint,
            "status": "Pending",
            "customer_email": ce,
        })

        row = self.db.get_dispute_by_case_id(case_id)
        ack = None
        if row:
            r = dict(row)
            ack = r.get("acknowledgement_number")
            try:
                send_complaint_registered_email(
                    to_addr=ce,
                    acknowledgement_number=ack or "",
                    customer_id=cid,
                    case_id=case_id,
                )
            except Exception:
                pass

        return {
            "case_id": case_id,
            "transaction": txn,
            "complaint": complaint,
            "customer_id": cid,
            "acknowledgement_number": ack,
        }

    def update_dispute_analysis(self, case_id, classification, fraud_score, summary, recommendation):
        self.db.update_dispute(case_id, {
            "classification": classification,
            "fraud_score": fraud_score,
            "ai_summary": summary,
            "recommendation": recommendation
        })
