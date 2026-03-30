import spacy

nlp = spacy.load("en_core_web_sm")


class NLPProcessor:
    def __init__(self):
        self.dispute_keywords = {
            "unauthorized": "Unauthorized Transaction",
            "not authorize": "Unauthorized Transaction",
            "fraud": "Unauthorized Transaction",
            "duplicate": "Duplicate Charge",
            "charged twice": "Duplicate Charge",
            "twice": "Duplicate Charge",
            "subscription": "Subscription Billing Issue",
            "recurring": "Subscription Billing Issue",
            "merchant": "Fraudulent Merchant",
            "scam": "Fraudulent Merchant"
        }

    def extract_entities(self, text: str):
        doc = nlp(text)

        entities = {
            "amounts": [],
            "dates": [],
            "organizations": []
        }

        for ent in doc.ents:
            if ent.label_ == "MONEY":
                entities["amounts"].append(ent.text)
            elif ent.label_ == "DATE":
                entities["dates"].append(ent.text)
            elif ent.label_ == "ORG":
                entities["organizations"].append(ent.text)

        return entities

    def classify_dispute(self, text: str):
        text_lower = text.lower()

        for keyword, label in self.dispute_keywords.items():
            if keyword in text_lower:
                return label

        return "Unknown"

    def process(self, text: str):
        entities = self.extract_entities(text)
        classification = self.classify_dispute(text)

        fraud_indicators = []
        if "unauthorized" in text.lower() or "fraud" in text.lower():
            fraud_indicators.append("suspicious_transaction")
        if "not recognize" in text.lower():
            fraud_indicators.append("unknown_merchant")

        return {
            "classification": classification,
            "entities": entities,
            "fraud_indicators": fraud_indicators
        }