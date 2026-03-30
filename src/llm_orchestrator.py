import os
from dotenv import load_dotenv
from openai import OpenAI
import streamlit as st


load_dotenv()


class LLMOrchestrator:
    def __init__(self):
        self.client = OpenAI(
            api_key = os.getenv("OPENROUTER_API_KEY") or st.secrets.get("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1"
        )

    def build_prompt(self, txn, nlp_output, fraud_output, complaint):
        return f"""
You are a financial fraud investigation assistant.

Transaction Details:
- Amount: {txn['amount']}
- Merchant: {txn['merchant_name']}
- Location: {txn['location']}

Customer Complaint:
"{complaint}"

NLP Analysis:
- Classification: {nlp_output['classification']}
- Fraud Indicators: {nlp_output['fraud_indicators']}

Fraud Analysis:
- Score: {fraud_output['fraud_score']}
- Risk Level: {fraud_output['risk_level']}

Tasks:
1. Write a concise investigation summary
2. Provide a clear resolution recommendation
"""

    def generate(self, txn, nlp_output, fraud_output, complaint):
        prompt = self.build_prompt(txn, nlp_output, fraud_output, complaint)

        response = self.client.chat.completions.create(
            model="stepfun/step-3.5-flash:free",  # FREE MODEL
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )

        return response.choices[0].message.content

    def parse_output(self, text: str):
        if "Recommendation:" in text:
            parts = text.split("Recommendation:")
            summary = parts[0].replace("Investigation Summary:", "").strip()
            recommendation = parts[1].strip()
        else:
            summary = text
            recommendation = ""

        return summary, recommendation