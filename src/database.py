import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from .ids import generate_acknowledgement_number
from .paths import data_path

DB_PATH = str(data_path("disputes.sqlite"))
_LOG = logging.getLogger(__name__)


class Database:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    @staticmethod
    def _ensure_column(conn, table: str, col: str, coltype: str) -> None:
        rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
        names = {r[1] for r in rows}
        if col not in names:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {coltype}")

    @staticmethod
    def _table_exists(conn, table: str) -> bool:
        row = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            (table,),
        ).fetchone()
        return row is not None

    def _backfill_acknowledgement_numbers(self, conn) -> None:
        rows = conn.execute(
            """
            SELECT case_id FROM disputes
            WHERE acknowledgement_number IS NULL OR TRIM(acknowledgement_number) = ''
            """
        ).fetchall()
        for r in rows:
            cid = r["case_id"]
            ack = f"ACK-LEGACY-{cid:06d}"
            conn.execute(
                "UPDATE disputes SET acknowledgement_number = ? WHERE case_id = ?",
                (ack, cid),
            )

    def _migrate_schema(self, conn) -> None:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS case_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id INTEGER NOT NULL,
                transaction_id TEXT NOT NULL,
                customer_id TEXT,
                verdict TEXT NOT NULL,
                decided_at TEXT NOT NULL,
                FOREIGN KEY (case_id) REFERENCES disputes(case_id)
            )
        """)
        if self._table_exists(conn, "disputes"):
            self._ensure_column(conn, "disputes", "resolved_at", "TEXT")
            self._ensure_column(conn, "disputes", "customer_email", "TEXT")
            self._ensure_column(conn, "disputes", "acknowledgement_number", "TEXT")
            self._backfill_acknowledgement_numbers(conn)

    @contextmanager
    def connect(self):
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        self._migrate_schema(conn)
        try:
            yield conn
        finally:
            conn.commit()
            conn.close()

    def initialize(self):
        with self.connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    transaction_id TEXT PRIMARY KEY,
                    customer_id TEXT,
                    amount REAL,
                    merchant_name TEXT,
                    location TEXT,
                    date_time TEXT
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS disputes (
                    case_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transaction_id TEXT,
                    complaint_text TEXT,
                    classification TEXT,
                    fraud_score REAL,
                    ai_summary TEXT,
                    recommendation TEXT,
                    status TEXT DEFAULT 'Pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id)
                )
            """)
            self._migrate_schema(conn)

    def insert_transaction(self, data: dict):
        with self.connect() as conn:
            conn.execute("""
                INSERT OR IGNORE INTO transactions 
                (transaction_id, customer_id, amount, merchant_name, location, date_time)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                data["transaction_id"],
                data.get("customer_id"),
                data["amount"],
                data["merchant_name"],
                data["location"],
                data["date_time"]
            ))

    def update_transaction_customer_id(self, transaction_id: str, customer_id: str) -> None:
        with self.connect() as conn:
            conn.execute(
                "UPDATE transactions SET customer_id = ? WHERE transaction_id = ?",
                (customer_id, transaction_id),
            )

    def get_transaction(self, transaction_id: str):
        with self.connect() as conn:
            return conn.execute(
                "SELECT * FROM transactions WHERE transaction_id = ?",
                (transaction_id,)
            ).fetchone()

    def insert_dispute(self, data: dict):
        with self.connect() as conn:
            ack = (data.get("acknowledgement_number") or "").strip()
            if not ack:
                for _ in range(16):
                    cand = generate_acknowledgement_number()
                    dup = conn.execute(
                        "SELECT 1 FROM disputes WHERE acknowledgement_number = ? LIMIT 1",
                        (cand,),
                    ).fetchone()
                    if not dup:
                        ack = cand
                        break
                if not ack:
                    ack = generate_acknowledgement_number()
            cursor = conn.execute("""
                INSERT INTO disputes 
                (transaction_id, complaint_text, classification, fraud_score, ai_summary, recommendation, status, customer_email, acknowledgement_number)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data["transaction_id"],
                data["complaint_text"],
                data.get("classification"),
                data.get("fraud_score"),
                data.get("ai_summary"),
                data.get("recommendation"),
                data.get("status", "Pending"),
                data.get("customer_email"),
                ack,
            ))
            return cursor.lastrowid

    def get_dispute_by_case_id(self, case_id: int):
        with self.connect() as conn:
            return conn.execute(
                """
                SELECT d.*, t.customer_id AS t_customer_id
                FROM disputes d
                INNER JOIN transactions t ON d.transaction_id = t.transaction_id
                WHERE d.case_id = ?
                """,
                (case_id,),
            ).fetchone()

    def get_all_disputes(self):
        with self.connect() as conn:
            return conn.execute(
                "SELECT * FROM disputes ORDER BY case_id DESC"
            ).fetchall()

    def get_disputes_by_customer(self, customer_id: str):
        with self.connect() as conn:
            return conn.execute("""
                SELECT d.*, t.customer_id AS t_customer_id FROM disputes d
                INNER JOIN transactions t ON d.transaction_id = t.transaction_id
                WHERE t.customer_id = ?
                ORDER BY d.case_id DESC
            """, (customer_id,)).fetchall()

    def get_dispute_detail_by_acknowledgement(self, acknowledgement_number: str):
        with self.connect() as conn:
            return conn.execute(
                """
                SELECT d.*, t.customer_id AS t_customer_id
                FROM disputes d
                INNER JOIN transactions t ON d.transaction_id = t.transaction_id
                WHERE d.acknowledgement_number = ?
                LIMIT 1
                """,
                ((acknowledgement_number or "").strip(),),
            ).fetchone()

    def get_case_decisions(self, limit: int = 500):
        with self.connect() as conn:
            return conn.execute(
                """
                SELECT * FROM case_decisions
                ORDER BY datetime(decided_at) DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

    def update_dispute_status(self, case_id: int, status: str):
        now = datetime.now(timezone.utc).isoformat()
        email_payload = None
        with self.connect() as conn:
            conn.execute(
                "UPDATE disputes SET status = ? WHERE case_id = ?",
                (status, case_id),
            )
            if status in ("Approved", "Rejected"):
                conn.execute(
                    "UPDATE disputes SET resolved_at = ? WHERE case_id = ?",
                    (now, case_id),
                )
                row = conn.execute(
                    """
                    SELECT d.case_id, d.transaction_id, d.complaint_text, d.ai_summary,
                           d.customer_email, d.acknowledgement_number,
                           t.customer_id AS t_customer_id
                    FROM disputes d
                    JOIN transactions t ON d.transaction_id = t.transaction_id
                    WHERE d.case_id = ?
                    """,
                    (case_id,),
                ).fetchone()
                if row:
                    r = dict(row)
                    conn.execute(
                        """
                        INSERT INTO case_decisions
                        (case_id, transaction_id, customer_id, verdict, decided_at)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            r["case_id"],
                            r["transaction_id"],
                            r.get("t_customer_id"),
                            status,
                            now,
                        ),
                    )
                    email_payload = {
                        "case_id": case_id,
                        "verdict": status,
                        "transaction_id": r["transaction_id"],
                        "customer_id": r.get("t_customer_id"),
                        "complaint_text": r.get("complaint_text"),
                        "ai_summary": r.get("ai_summary"),
                        "customer_email": r.get("customer_email"),
                        "acknowledgement_number": r.get("acknowledgement_number"),
                    }

        if email_payload:
            try:
                from src.email_notify import send_verdict_email

                send_verdict_email(email_payload)
            except Exception:
                _LOG.exception("Failed to send verdict email")

    def delete_dispute(self, case_id: int):
        with self.connect() as conn:
            conn.execute(
                "DELETE FROM disputes WHERE case_id = ?",
                (case_id,),
            )

    def update_dispute(self, case_id: int, data: dict):
        with self.connect() as conn:
            conn.execute("""
                UPDATE disputes
                SET classification = ?, fraud_score = ?, ai_summary = ?, recommendation = ?
                WHERE case_id = ?
            """, (
                data.get("classification"),
                data.get("fraud_score"),
                data.get("ai_summary"),
                data.get("recommendation"),
                case_id
            ))
