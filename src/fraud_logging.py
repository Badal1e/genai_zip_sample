from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .paths import logs_dir


def _append_jsonl(filename: str, record: dict) -> None:
    path: Path = logs_dir() / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def log_fraud_request(
    *,
    transaction_id: str | None,
    case_id: int | None,
    model_class_score: float | None,
    model_proba_positive: float | None,
    fraud_score_final: float,
    risk_level: str,
) -> None:
    _append_jsonl(
        "fraud_predictions.jsonl",
        {
            "ts": datetime.now(timezone.utc).isoformat(),
            "transaction_id": transaction_id,
            "case_id": case_id,
            "model_class_score": model_class_score,
            "model_proba_positive": model_proba_positive,
            "fraud_score_final": fraud_score_final,
            "risk_level": risk_level,
        },
    )


def log_train_metrics(
    *,
    n_samples: int,
    n_train: int,
    n_val: int,
    accuracy: float,
    precision: float,
    recall: float,
    source: str,
) -> None:
    # Same wording as Agent dashboard caption after "Train fraud model from database"
    summary = (
        f"Validation — accuracy: {accuracy:.3f}, precision: {precision:.3f}, "
        f"recall: {recall:.3f} (train={n_train}, val={n_val})"
    )
    _append_jsonl(
        "model_train_metrics.jsonl",
        {
            "ts": datetime.now(timezone.utc).isoformat(),
            "source": source,
            "n_samples": n_samples,
            "n_train": n_train,
            "n_val": n_val,
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "summary": summary,
        },
    )
