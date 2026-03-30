import joblib

from .fraud_logging import log_fraud_request
from .paths import models_dir, models_path


class FraudEngine:
    def __init__(self):
        models_dir().mkdir(parents=True, exist_ok=True)
        model_path = models_path("fraud_model.pkl")

        if not model_path.exists():
            from models.train_fraud_model import train_model

            train_model()

        if not model_path.exists():
            raise Exception("Model file not created properly!")

        self.model = joblib.load(str(model_path))

    def _prepare_features(self, txn):
        return [[txn["amount"]]]

    def predict(self, txn, complaint="", case_id=None):
        features = self._prepare_features(txn)
        txn_id = txn.get("transaction_id") if isinstance(txn, dict) else None

        model_class_score = None
        model_proba_positive = None

        try:
            model_class_score = float(self.model.predict(features)[0])
        except Exception:
            model_class_score = 0.2

        try:
            proba = self.model.predict_proba(features)[0]
            if len(proba) > 1:
                model_proba_positive = float(proba[1])
            else:
                model_proba_positive = float(proba[0])
        except Exception:
            pass

        score = model_class_score if model_class_score is not None else 0.2

        text = (complaint or "").lower()

        if any(word in text for word in ["unauthorized", "fraud", "not mine"]):
            score = max(score, 0.9)

        elif any(word in text for word in ["duplicate", "twice", "double"]):
            score = max(score, 0.5)

        elif any(word in text for word in ["refund", "not returned"]):
            score = max(score, 0.3)

        amount = txn.get("amount", 0) if isinstance(txn, dict) else 0

        if amount > 20000:
            score = max(score, 0.85)
        elif amount > 10000:
            score = max(score, 0.6)

        if score > 0.75:
            risk = "High"
        elif score > 0.4:
            risk = "Medium"
        else:
            risk = "Low"

        fraud_indicators = []

        if score > 0.75:
            fraud_indicators.append("High risk transaction")
        elif score > 0.4:
            fraud_indicators.append("Suspicious behavior")
        else:
            fraud_indicators.append("Low risk")

        final_score = round(score, 2)

        try:
            log_fraud_request(
                transaction_id=txn_id,
                case_id=case_id,
                model_class_score=model_class_score,
                model_proba_positive=model_proba_positive,
                fraud_score_final=final_score,
                risk_level=risk,
            )
        except Exception:
            pass

        return {
            "fraud_score": final_score,
            "risk_level": risk,
            "fraud_indicators": fraud_indicators,
        }
