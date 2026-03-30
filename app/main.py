import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st

from app.ui_theme import bordered, inject_styles, sidebar_nav

st.set_page_config(page_title="GenAI Dispute Assistant", layout="wide")
inject_styles()
sidebar_nav()

st.title("Payment dispute desk")
st.caption("Customers file disputes; agents review. Track status with your acknowledgement number.")

st.markdown(
    """
<div class="home-intro">
<p class="home-kicker">What this is</p>
<p class="home-lead">Describe the problem, pull up the charge, see AI summary and risk, then approve or reject. Status lives here instead of email threads.</p>
</div>
""",
    unsafe_allow_html=True,
)

st.subheader("Shortcuts")
st.caption("Same pages as the sidebar.")

_app = Path(__file__).resolve().parent
links = [
    ("customer_portal.py", "Customer portal", "File a dispute.", "Open customer portal"),
    ("agent_dashboard.py", "Agent dashboard", "CSV, lookup, analysis, queue.", "Open agent dashboard"),
    ("login.py", "Case status", "Look up by acknowledgement number.", "Check case status"),
]
for col, (fn, head, sub, lbl) in zip(st.columns(3), links):
    with col:
        with bordered():
            st.subheader(head)
            st.caption(sub)
            st.page_link(str(_app / "pages" / fn), label=lbl, use_container_width=True)
