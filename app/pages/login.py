import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pandas as pd
import streamlit as st

from app.ui_theme import bordered, inject_styles, sidebar_nav
from src.database import Database

st.set_page_config(page_title="Case status", layout="centered", page_icon="")
inject_styles()
sidebar_nav()

db = Database()

st.markdown(
    """
<div class="case-status-intro">
<p>Enter your <strong>acknowledgement number</strong> (e.g. from your confirmation email). </p>
<p class="legacy-hint">If your case was filed before acknowledgement numbers were issued, you can still look up with your <strong>customer ID</strong>.</p>
</div>
""",
    unsafe_allow_html=True,
)
st.title("Check your cases")

ack_or_legacy = st.text_input(
    "Acknowledgement number or customer ID",
    placeholder="ACK-… or e.g. CUST1001",
    key="ack_lookup",
)

if st.button("View my cases", type="primary", use_container_width=True):
    if not (ack_or_legacy or "").strip():
        st.error("Enter your acknowledgement number or customer ID.")
        st.stop()

    raw = ack_or_legacy.strip()
    cases = []

    row = db.get_dispute_detail_by_acknowledgement(raw)
    if row:
        cases = [dict(row)]
    else:
        rows = db.get_disputes_by_customer(raw)
        cases = [dict(r) for r in rows]

    if not cases:
        st.info("No cases found. Check the value or file a new dispute from the customer portal.")
    else:
        st.success("Found your case(s).")

        st.metric("Disputes", len(cases))
        tx = {c.get("transaction_id") for c in cases if c.get("transaction_id")}
        st.caption(f"{len(tx)} transaction ID(s).")

        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Acknowledgement": c.get("acknowledgement_number") or "—",
                        "Case": c.get("case_id"),
                        "Transaction ID": c.get("transaction_id"),
                        "Status": c.get("status") or "—",
                        "Fraud score": c.get("fraud_score") if c.get("fraud_score") is not None else "—",
                        "Classification": c.get("classification") or "—",
                    }
                    for c in cases
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("### Details")
        for case in cases:
            with bordered():
                ack = case.get("acknowledgement_number") or "—"
                st.markdown(f"**{ack}** · Case **{case['case_id']}** · `{case['transaction_id']}`")
                a, b = st.columns(2)
                a.markdown(f"**Status**  \n{case.get('status') or '—'}")
                b.markdown(
                    f"**Fraud score**  \n{case.get('fraud_score') if case.get('fraud_score') is not None else '—'}"
                )
                a, b = st.columns(2)
                a.markdown(f"**Classification**  \n{case.get('classification') or '—'}")
                b.markdown(
                    f"**Customer ID**  \n{case.get('t_customer_id') or '—'}"
                )
                summary = case.get("ai_summary") or ""
                if summary:
                    st.markdown("**Summary**")
                    st.caption(summary[:500] + ("…" if len(summary) > 500 else ""))

                s = case.get("status") or ""
                if s == "Approved":
                    st.success("Approved")
                elif s == "Rejected":
                    st.error("Rejected")
                else:
                    st.warning("Pending")
