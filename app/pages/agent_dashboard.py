import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pandas as pd
import streamlit as st

from app.ui_theme import bordered, inject_styles, show_transaction, sidebar_nav
from src.csv_import import validate_transaction_csv_df
from src.database import Database
from src.fraud_engine import FraudEngine
from src.llm_orchestrator import LLMOrchestrator
from src.nlp_processor import NLPProcessor

st.set_page_config(page_title="Agent dashboard", layout="wide", page_icon="")
inject_styles()
sidebar_nav()

if "pending_delete" not in st.session_state:
    st.session_state.pending_delete = None
if "last_import_df" not in st.session_state:
    st.session_state.last_import_df = None

st.title("Agent dashboard")
st.markdown(
    """
<div class="agent-welcome"><p>Import data, look up a charge, run analysis, work the queue.</p></div>
""",
    unsafe_allow_html=True,
)

db = Database()
COLS = ["transaction_id", "customer_id", "amount", "merchant_name", "location", "date_time"]

t1, t2, t3 = st.tabs(["Data & model", "Look up & case", "Queue & history"])

with t1:
    st.subheader("CSV & model")
    st.caption("Columns: " + ", ".join(COLS))
    with bordered():
        f = st.file_uploader("CSV", type=["csv"])
        st.caption(
            "Required columns: "
            + ", ".join(COLS)
            + ". Rows are imported for lookup; fraud scoring uses the bundled trained model (`models/fraud_model.pkl`) without retraining from the UI."
        )
        do_import = st.button("Import", use_container_width=True)

        if do_import:
            if f is None:
                st.error("Pick a file first.")
            else:
                try:
                    df = pd.read_csv(f)
                    ok, err = validate_transaction_csv_df(df)
                    if not ok:
                        st.error(err)
                    else:
                        n = 0
                        for _, row in df.iterrows():
                            cid = row["customer_id"]
                            if pd.isna(cid):
                                cid = None
                            else:
                                cid = str(cid).strip() or None
                            db.insert_transaction(
                                {
                                    "transaction_id": str(row["transaction_id"]).strip(),
                                    "customer_id": cid,
                                    "amount": float(pd.to_numeric(row["amount"], errors="coerce")),
                                    "merchant_name": str(row["merchant_name"]),
                                    "location": str(row["location"]),
                                    "date_time": str(row["date_time"]),
                                }
                            )
                            n += 1
                        st.session_state.last_import_df = df[COLS].copy()
                        st.success(f"Imported {n} rows.")
                except Exception as e:
                    st.error(str(e))

    if st.session_state.last_import_df is not None:
        st.markdown("**Imported data** — scroll the table, click a cell to select, copy with ⌘C / Ctrl+C.")
        st.dataframe(
            st.session_state.last_import_df,
            use_container_width=True,
            hide_index=True,
            height=420,
        )
        if st.button("Clear table preview", key="clear_import_preview"):
            st.session_state.last_import_df = None
            st.rerun()

with t2:
    u1, u2 = st.tabs(["Lookup", "Analyze"])

    with u1:
        st.subheader("Lookup")
        with bordered():
            tid = st.text_input("Transaction ID", key="lookup_tid", placeholder="TXN…")
            if tid and tid.strip():
                row = db.get_transaction(tid.strip())
                if row:
                    st.success("Found.")
                    show_transaction(dict(row), "Transaction")
                else:
                    st.error("Not found.")

    with u2:
        st.subheader("Analyze → new case")
        with bordered():
            tid = st.text_input("Transaction ID", key="analyze_tid")
            complaint = st.text_area("Complaint", key="analyze_complaint", height=140)
            if st.button("Run", type="primary", key="run_analyze"):
                if not (tid or "").strip() or not (complaint or "").strip():
                    st.error("Need transaction ID and complaint text.")
                else:
                    txn_row = db.get_transaction(tid.strip())
                    if not txn_row:
                        st.error("Transaction not in DB.")
                    else:
                        txn = dict(txn_row)
                        try:
                            with st.spinner("Running…"):
                                nlp = NLPProcessor()
                                fraud = FraudEngine()
                                llm = LLMOrchestrator()
                                nlp_out = nlp.process(complaint)
                                fraud_out = fraud.predict(txn, complaint, case_id=None)
                                raw = llm.generate(txn, nlp_out, fraud_out, complaint)
                                summary, recommendation = llm.parse_output(raw)
                            c1, c2, c3 = st.columns(3)
                            c1.metric("Class", nlp_out["classification"])
                            c2.metric("Fraud score", round(float(fraud_out["fraud_score"]), 2))
                            c3.metric("Risk", fraud_out["risk_level"])
                            st.markdown("**Summary**")
                            st.write(summary)
                            st.markdown("**Recommendation**")
                            st.write(recommendation)
                            case_id = db.insert_dispute(
                                {
                                    "transaction_id": txn["transaction_id"],
                                    "complaint_text": complaint.strip(),
                                    "classification": nlp_out["classification"],
                                    "fraud_score": fraud_out["fraud_score"],
                                    "ai_summary": summary,
                                    "recommendation": recommendation,
                                    "status": "Pending",
                                }
                            )
                            st.success(f"Case **{case_id}** created (see Queue tab).")
                        except Exception as e:
                            st.error(str(e))

with t3:
    st.subheader("Status counts")
    disputes = [dict(d) for d in db.get_all_disputes()]
    if disputes:
        df = pd.DataFrame(disputes)
        if "status" in df.columns and not df["status"].isna().all():
            vc = df["status"].value_counts(dropna=True)
            if not vc.empty:
                st.bar_chart(vc)
    else:
        st.caption("No disputes yet.")

    st.divider()
    st.subheader("Decision history")
    hist = db.get_case_decisions(limit=500)
    if hist:
        hdf = pd.DataFrame([dict(r) for r in hist])
        st.dataframe(hdf, use_container_width=True, hide_index=True)
        st.download_button(
            "Download CSV",
            hdf.to_csv(index=False).encode("utf-8"),
            "case_decisions.csv",
            "text/csv",
        )
    else:
        st.caption("No decisions yet.")

    st.divider()
    st.subheader("Cases")
    filt = st.selectbox("Filter", ["All", "Pending", "Approved", "Rejected"])
    rows = disputes if filt == "All" else [d for d in disputes if d.get("status") == filt]

    if not rows:
        st.info("Nothing to show.")
    for i, d in enumerate(rows):
        with bordered():
            st.markdown(f"**Case {d['case_id']}** · `{d.get('transaction_id', '')}`")
            a, b = st.columns(2)
            a.write(f"**Status:** {d.get('status', '—')}")
            b.write(f"Fraud score: {d.get('fraud_score', '—')}")
            with st.expander("JSON"):
                st.json(d)
            pid = d["case_id"]
            if d.get("status") == "Pending":
                x, y = st.columns(2)
                if x.button("Approve", key=f"a_{pid}_{i}", use_container_width=True):
                    db.update_dispute_status(pid, "Approved")
                    st.rerun()
                if y.button("Reject", key=f"r_{pid}_{i}", use_container_width=True):
                    db.update_dispute_status(pid, "Rejected")
                    st.rerun()
            if st.session_state.pending_delete == pid:
                st.warning(f"Delete case **{pid}**?")
                x, y = st.columns(2)
                if x.button("Yes", key=f"yd_{pid}_{i}", use_container_width=True):
                    db.delete_dispute(pid)
                    st.session_state.pending_delete = None
                    st.rerun()
                if y.button("Cancel", key=f"nd_{pid}_{i}", use_container_width=True):
                    st.session_state.pending_delete = None
                    st.rerun()
            elif st.button("Delete", key=f"d_{pid}_{i}", use_container_width=True):
                st.session_state.pending_delete = pid
                st.rerun()
