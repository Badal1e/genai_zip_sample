"""Shared styles + sidebar for Streamlit pages."""
from pathlib import Path
from typing import Any

import streamlit as st

_APP = Path(__file__).resolve().parent


def inject_styles() -> None:
    st.markdown(
        """
<style>
/* Light, calm palette — avoids “default dark AI” look */
:root {
  --desk-bg-top: #f0f7ff;
  --desk-bg-bottom: #faf8ff;
  --desk-text: #0f172a;
  --desk-muted: #64748b;
  --desk-accent: #0d9488;
  --desk-accent-soft: rgba(13, 148, 136, 0.12);
  --desk-card: #ffffff;
  --desk-border: rgba(15, 23, 42, 0.08);
  --desk-shadow: 0 4px 24px rgba(15, 23, 42, 0.06);
}

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}

@keyframes deskFadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes deskHeroBar {
  from { transform: scaleX(0.35); opacity: 0.6; }
  to { transform: scaleX(1); opacity: 1; }
}

[data-testid="stAppViewContainer"] {
  background: linear-gradient(165deg, var(--desk-bg-top) 0%, var(--desk-bg-bottom) 55%, #fff 100%) !important;
  color: var(--desk-text) !important;
}

[data-testid="stHeader"] {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(8px);
}

[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%) !important;
  border-right: 1px solid var(--desk-border) !important;
}

[data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] span {
  color: var(--desk-text) !important;
}

.block-container {
  padding-top: 1.5rem;
  animation: deskFadeIn 0.5s ease-out;
}

h1, h2, h3 {
  color: var(--desk-text) !important;
  font-weight: 650 !important;
  letter-spacing: -0.02em;
}

[data-testid="stVerticalBlockBorderWrapper"] {
  background: var(--desk-card) !important;
  border: 1px solid var(--desk-border) !important;
  border-radius: 18px !important;
  box-shadow: var(--desk-shadow) !important;
  margin-bottom: 1rem !important;
  animation: deskFadeIn 0.55s ease-out backwards;
  transition: box-shadow 0.25s ease, border-color 0.25s ease, transform 0.2s ease;
}

[data-testid="stVerticalBlockBorderWrapper"]:hover {
  border-color: rgba(13, 148, 136, 0.25) !important;
  box-shadow: 0 12px 36px rgba(15, 23, 42, 0.08) !important;
}

[data-testid="stVerticalBlockBorderWrapper"]:nth-child(1) { animation-delay: 0.05s; }
[data-testid="stVerticalBlockBorderWrapper"]:nth-child(2) { animation-delay: 0.1s; }
[data-testid="stVerticalBlockBorderWrapper"]:nth-child(3) { animation-delay: 0.15s; }

button[kind="primary"] {
  transition: transform 0.2s ease, box-shadow 0.2s ease !important;
}

button[kind="primary"]:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(13, 148, 136, 0.35) !important;
}

/* Success / info banners — lighter chrome */
[data-testid="stAlert"] {
  border-radius: 14px !important;
  animation: deskFadeIn 0.4s ease-out;
}

.home-intro {
  margin: 0 0 1.75rem 0;
  padding: 1.25rem 1.35rem;
  background: var(--desk-card);
  border: 1px solid var(--desk-border);
  border-radius: 18px;
  box-shadow: var(--desk-shadow);
  max-width: 42rem;
  animation: deskFadeIn 0.6s ease-out;
}

.home-intro::before {
  content: "";
  display: block;
  width: 100%;
  max-width: 120px;
  height: 4px;
  border-radius: 4px;
  background: linear-gradient(90deg, #0d9488, #38bdf8, #818cf8);
  margin-bottom: 1rem;
  transform-origin: left;
  animation: deskHeroBar 0.7s ease-out;
}

.home-kicker {
  margin: 0 0 0.4rem 0;
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--desk-accent) !important;
}

.home-lead {
  margin: 0;
  font-size: 1.06rem;
  line-height: 1.65;
  color: var(--desk-muted) !important;
}

.agent-welcome {
  background: linear-gradient(135deg, rgba(13, 148, 136, 0.08), rgba(56, 189, 248, 0.06));
  border: 1px solid rgba(13, 148, 136, 0.2);
  padding: 1.25rem 1.4rem;
  border-radius: 18px;
  margin-bottom: 1.25rem;
  line-height: 1.55;
  animation: deskFadeIn 0.5s ease-out;
}

.agent-welcome p { margin: 0; color: var(--desk-muted) !important; }

.case-status-intro {
  margin: 0 0 1.25rem 0;
  padding: 1rem 1.15rem;
  background: var(--desk-card);
  border-radius: 14px;
  border: 1px solid var(--desk-border);
  max-width: 32rem;
  animation: deskFadeIn 0.5s ease-out;
}

.case-status-intro p {
  margin: 0 0 0.5rem 0;
  font-size: 0.95rem;
  line-height: 1.55;
  color: var(--desk-muted) !important;
}

.case-status-intro p:last-child { margin-bottom: 0; }

.legacy-hint { font-size: 0.88rem !important; opacity: 0.92; }

/* Radio / tabs feel a bit more tactile */
[data-baseweb="radio"] label {
  transition: color 0.2s ease;
}

[data-testid="stTabs"] [data-baseweb="tab"] {
  transition: border-color 0.2s ease, color 0.2s ease;
}
</style>
""",
        unsafe_allow_html=True,
    )


def bordered():
    try:
        return st.container(border=True)
    except TypeError:
        return st.container()


def sidebar_nav() -> None:
    with st.sidebar:
        st.markdown("### Menu")
        st.page_link(str(_APP / "main.py"), label="Home")
        st.page_link(str(_APP / "pages" / "customer_portal.py"), label="Customer portal")
        st.page_link(str(_APP / "pages" / "agent_dashboard.py"), label="Agent dashboard")
        st.page_link(str(_APP / "pages" / "login.py"), label="Case status")
        st.divider()
        st.caption("Dispute desk")


def txn_fields(txn: dict[str, Any]) -> list[tuple[str, str]]:
    return [
        ("Transaction ID", str(txn.get("transaction_id", "—"))),
        ("Customer ID", str(txn.get("customer_id", "—"))),
        ("Amount", f"{float(txn.get('amount', 0) or 0):,.2f}"),
        ("Merchant", str(txn.get("merchant_name", "—"))),
        ("Location", str(txn.get("location", "—"))),
        ("Date / time", str(txn.get("date_time", "—"))),
    ]


def show_transaction(txn: dict[str, Any], title: str = "Transaction") -> None:
    st.markdown(f"**{title}**")
    c1, c2 = st.columns(2)
    rows = txn_fields(txn)
    half = (len(rows) + 1) // 2
    for i, (label, val) in enumerate(rows):
        (c1 if i < half else c2).markdown(f"**{label}**  \n{val}")
