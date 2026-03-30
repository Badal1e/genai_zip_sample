import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.ui_theme import bordered, inject_styles, sidebar_nav

from datetime import date, datetime

import streamlit as st

from src.email_notify import looks_like_email
from src.ingestion import IngestionService
from src.nlp_processor import NLPProcessor
from src.fraud_engine import FraudEngine
from src.llm_orchestrator import LLMOrchestrator

st.set_page_config(page_title="Customer portal", layout="wide", page_icon="")

inject_styles()
sidebar_nav()

if "customer_result" not in st.session_state:
    st.session_state.customer_result = None

st.title("Tell us what happened")
st.caption("We will match your charge, read your message, and route it to the team. Plain language is perfect.")

_, head2 = st.columns([4, 1])
with head2:
    if st.button("View case status", use_container_width=True):
        st.switch_page(str(Path(__file__).resolve().parent / "login.py"))

with bordered():
    st.subheader("Start here")

    mode = st.radio(
        "How do you want to reference the transaction?",
        ["Use existing transaction", "Manual entry (not on file yet)"],
        horizontal=True,
    )

    transaction_id = st.text_input("Transaction ID", placeholder="e.g. TXN123456")
    complaint = st.text_area(
        "Describe your issue",
        placeholder="What happened? Include any details that help us investigate.",
        height=120,
    )
    contact_email = st.text_input(
        "Email (for acknowledgement and case updates)",
        placeholder="you@example.com",
        help="We send your acknowledgement number, customer ID, and resolution status to this address.",
    )

    amount = 0.0
    merchant = ""
    location = ""
    combined_dt = datetime.now()

    if mode == "Manual entry (not on file yet)":
        st.caption(
            "Manual entry is for charges not yet in our system. We still need merchant and location details."
        )
        c1, c2 = st.columns(2)
        amount = c1.number_input("Amount", min_value=0.0, format="%.2f")
        merchant = c2.text_input("Merchant")
        c1, c2 = st.columns(2)
        location = c1.text_input("Location")
        d = c2.date_input("Transaction date", value=date.today())
        t = st.time_input("Time", value=datetime.now().time())
        combined_dt = datetime.combine(d, t)

submitted = st.button("Submit dispute", type="primary", use_container_width=False)

if submitted:
    try:
        if not transaction_id or not str(transaction_id).strip():
            st.error("Transaction ID is required.")
            st.stop()
        if not complaint or not str(complaint).strip():
            st.error("Please describe your issue.")
            st.stop()
        if not contact_email or not looks_like_email(str(contact_email)):
            st.error("Enter a valid email address for acknowledgement and updates.")
            st.stop()

        if mode == "Manual entry (not on file yet)":
            if not merchant or not str(merchant).strip():
                st.error("Merchant is required for manual entry.")
                st.stop()
            if not location or not str(location).strip():
                st.error("Location is required for manual entry.")
                st.stop()

        ingestion = IngestionService()
        tid = str(transaction_id).strip()

        if mode == "Manual entry (not on file yet)":
            existing = ingestion.db.get_transaction(tid)
            if existing:
                st.error(
                    "This transaction ID is already on file. Use “Use existing transaction” instead."
                )
                st.stop()
            manual_txn = {
                "amount": float(amount),
                "merchant_name": str(merchant).strip(),
                "location": str(location).strip(),
                "date_time": combined_dt.isoformat(),
            }
            data = ingestion.create_dispute(
                tid,
                str(complaint).strip(),
                str(contact_email).strip(),
                manual_txn=manual_txn,
            )
        else:
            data = ingestion.create_dispute(
                tid,
                str(complaint).strip(),
                str(contact_email).strip(),
            )

        txn = data["transaction"]
        case_id = data["case_id"]
        nlp = NLPProcessor()
        fraud = FraudEngine()
        llm = LLMOrchestrator()

        with st.spinner("Analyzing your dispute…"):
            nlp_out = nlp.process(complaint)
            fraud_out = fraud.predict(txn, complaint, case_id=case_id)
            llm_raw = llm.generate(txn, nlp_out, fraud_out, complaint)
            summary, recommendation = llm.parse_output(llm_raw)

            ingestion.update_dispute_analysis(
                case_id,
                nlp_out["classification"],
                fraud_out["fraud_score"],
                summary,
                recommendation,
            )

        st.session_state.customer_result = {
            "case_id": case_id,
            "acknowledgement_number": data.get("acknowledgement_number"),
            "customer_id": data.get("customer_id"),
            "nlp_out": nlp_out,
            "fraud_out": fraud_out,
            "summary": summary,
            "recommendation": recommendation,
        }
        st.success("Dispute received and analyzed.")
        st.rerun()

    except Exception as e:
        st.error(str(e))

if st.session_state.customer_result:
    r = st.session_state.customer_result
    with bordered():
        st.subheader("Analysis results")
        ack = r.get("acknowledgement_number") or "—"
        cid = r.get("customer_id") or "—"
        st.caption(
            f"Acknowledgement **{ack}** · Customer ID **{cid}** · Case **{r['case_id']}** — save these for follow-up."
        )

        m1, m2, m3 = st.columns(3)
        m1.metric("Classification", r["nlp_out"]["classification"])
        m2.metric("Fraud score", round(float(r["fraud_out"]["fraud_score"]), 2))
        m3.metric("Risk level", r["fraud_out"]["risk_level"])

        risk = r["fraud_out"]["risk_level"]
        if risk == "High":
            st.error("High risk — this transaction may need urgent review.")
        elif risk == "Medium":
            st.warning("Medium risk — additional verification may help.")
        else:
            st.success("Lower risk based on current signals.")

        st.markdown("**Investigation summary**")
        st.write(r["summary"])
        st.markdown("**Recommendation**")
        st.write(r["recommendation"])

        st.info(
            "**What happens next:** Check **Case status** with your acknowledgement number. "
            "If SMTP is configured, you will receive email at the address you provided when the case is decided."
        )

    if st.button("Dismiss results"):
        st.session_state.customer_result = None
        st.rerun()
