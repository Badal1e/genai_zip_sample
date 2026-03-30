# GenAI fraud detection — Streamlit app

Streamlit UI for payment disputes: customers file issues, agents import transactions, run NLP + fraud scoring + LLM summary, approve/reject cases, and optional email (acknowledgement on submit + verdict on decision).

## What you need

- **Python 3.9+** (3.9 is tested with the pinned SpaCy stack)
- This repository cloned or unzipped on your machine

## Setup

### 1. Virtual environment

From the **repository root** (the folder that contains `app/`, `src/`, and `requirements.txt`):

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This installs Streamlit, pandas/scikit-learn, SpaCy + `en_core_web_sm` (via the wheel URL in `requirements.txt`), OpenAI client (for OpenRouter), and optional `yagmail` for SMTP.

### 3. Environment variables

Copy the example file and edit it (do not commit real keys):

```bash
cp .env.example .env
```

| Variable | Purpose |
|----------|---------|
| `OPENROUTER_API_KEY` | Required for LLM summaries (OpenRouter API). |
| `EMAIL_ENABLED` | Set to `false` to skip sending emails. |
| `SMTP_*` | If email is enabled, Gmail (or other SMTP) for registration and verdict notifications. |

### 4. SQLite database

Initialize tables (must run from the **repository root** so `src` is a package):

```bash
python -m src.init_db
```

The DB file is created under `data/disputes.sqlite` (see `src/paths.py`).

If `data/raw_transactions.csv` exists, the same command also loads those rows into the `transactions` table (the app looks up transaction IDs in SQLite, not directly in the CSV).

### 5. Run the app

From the **repository root**:

```bash
streamlit run app/main.py
```

Open the URL Streamlit prints (usually `http://localhost:8501`).

**Sidebar navigation:** the app uses a custom menu. In `.streamlit/config.toml`, `showSidebarNavigation = false` hides Streamlit’s duplicate auto page list (needs a recent Streamlit, e.g. 1.33+).

### Deploy on Streamlit Community Cloud

You can host this app on **[Streamlit Community Cloud](https://streamlit.io/cloud)** (free tier available):

1. Push the repo to **GitHub** (keep `.env` out of git; use `.gitignore`).
2. In Cloud, **New app** → pick the repo, branch, and **Main file path**: `app/main.py`.
3. Under **Secrets**, add TOML matching your `.env`, for example:
   ```toml
   OPENROUTER_API_KEY = "your-key"
   EMAIL_ENABLED = "false"
   SMTP_HOST = ""
   SMTP_PORT = "587"
   SMTP_USER = ""
   SMTP_PASSWORD = ""
   ```
4. Deploy. The build uses `requirements.txt`. **Note:** the default SQLite file under `data/` is **ephemeral** on Cloud (resets when the app sleeps or restarts). For production persistence use an external database or object storage; for demos, run `python -m src.init_db` via a one-off job or accept a fresh DB per session.

Secrets are read in code via `st.secrets` where implemented (e.g. LLM key) and `python-dotenv` locally.

## Project layout (short)

| Path | Role |
|------|------|
| `app/main.py` | Home |
| `app/pages/` | Customer portal, agent dashboard, case status (`login.py`) |
| `app/ui_theme.py` | Shared CSS + sidebar |
| `src/` | DB, ingestion, NLP, fraud model, LLM, email |
| `data/` | SQLite DB, sample CSV |
| `models/` | Fraud model training script |

## Optional: regenerate sample transactions

If you use the bundled generator:

```bash
python -m data.generate_data
```

(Module name is `data.generate_data`, not `generate_data.py`.)

## Troubleshooting

- **Import / path errors:** Always run `streamlit run app/main.py` from the project root so `app` and `src` resolve correctly.
- **Database init:** Use `python -m src.init_db` from the project root (not `python init_db.py` inside `src/` alone — package imports require the module form).
- **SpaCy model:** Reinstall with `pip install -r requirements.txt` if `en_core_web_sm` is missing.
- **LLM errors:** Confirm `OPENROUTER_API_KEY` in `.env` and network access to OpenRouter.

## Zip of the source

A distributable archive can exclude the virtualenv and caches, for example:

```bash
zip -r project.zip . \
  -x "*.venv/*" -x "*__pycache__/*" -x "*.pyc" -x ".git/*" -x "*/.env"
```

Keep your real `.env` out of the zip; use `.env.example` as a template.
