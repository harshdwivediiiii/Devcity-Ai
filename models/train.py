import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.metrics import classification_report, f1_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler


BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from db import db_init, get_snapshot_files  # noqa: E402
from model_loader import invalidate_cache  # noqa: E402


LOGGER = logging.getLogger(__name__)
ARTEFACTS_DIR = BASE_DIR / "models" / "artefacts"
FEATURE_COLS = [
    "size",
    "byte_size",
    "complexity",
    "function_count",
    "avg_params",
    "depth",
    "churn",
    "bug_churn",
    "fan_out",
]


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train DevCity AI models from a snapshot.")
    parser.add_argument("--snapshot", required=True, help="Snapshot ID to train from.")
    parser.add_argument(
        "--strategy",
        choices=["threshold", "git_history"],
        default="threshold",
        help="Label generation strategy.",
    )
    return parser.parse_args(argv)


def load_training_frame(snapshot_id: str) -> pd.DataFrame:
    db_init()
    rows = get_snapshot_files(snapshot_id)
    if not rows:
        raise ValueError(f"No file metrics found for snapshot {snapshot_id}.")

    frame = pd.DataFrame(rows).fillna(0)
    for column in FEATURE_COLS:
        if column not in frame.columns:
            frame[column] = 0
    frame = frame[frame["size"] != 0].copy()
    if frame.empty:
        raise ValueError(f"Snapshot {snapshot_id} has no non-empty files to train on.")
    return frame


def build_labels(frame: pd.DataFrame, strategy: str) -> tuple[pd.Series, str]:
    if strategy == "git_history":
        threshold = frame["bug_churn"].quantile(0.75)
        labels = (frame["bug_churn"] >= threshold).astype(int)
        return labels, "git_history (bug-fix commit P75)"

    labels = (
        (frame["complexity"] > 10)
        | (frame["size"] > 300)
        | (frame["function_count"] > 20)
        | (frame["avg_params"] > 5)
    ).astype(int)
    return labels, "threshold (rule distillation)"


def train_models(snapshot_id: str, strategy: str) -> dict[str, Any]:
    frame = load_training_frame(snapshot_id)
    labels, label_strategy = build_labels(frame, strategy)
    class_counts = labels.value_counts()
    if len(class_counts) < 2 or int(class_counts.min()) < 2:
        raise ValueError(
            "Training requires at least two classes with two or more samples each."
        )

    features = frame[FEATURE_COLS].values
    target = labels.values
    x_train, x_test, y_train, y_test = train_test_split(
        features,
        target,
        test_size=0.2,
        random_state=42,
        stratify=target,
    )

    scaler = StandardScaler().fit(x_train)
    x_train_scaled = scaler.transform(x_train)
    x_test_scaled = scaler.transform(x_test)

    classifier = RandomForestClassifier(
        n_estimators=100,
        class_weight="balanced",
        random_state=42,
    ).fit(x_train_scaled, y_train)

    report = classification_report(y_test, classifier.predict(x_test_scaled))
    LOGGER.info("%s", report)
    risk_f1 = f1_score(y_test, classifier.predict(x_test_scaled), average="weighted")

    contamination = max(0.01, min(0.5, float(labels.mean())))
    anomaly_model = IsolationForest(
        contamination=contamination,
        random_state=42,
    ).fit(scaler.transform(features))

    version = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    out_dir = ARTEFACTS_DIR / version
    out_dir.mkdir(parents=True, exist_ok=True)

    joblib.dump((scaler, classifier), out_dir / "risk_model.joblib")
    joblib.dump(anomaly_model, out_dir / "anomaly_model.joblib")

    trained_at = datetime.utcnow().isoformat() + "Z"
    meta = {
        "version": version,
        "trained_at": trained_at,
        "snapshot_id": snapshot_id,
        "label_strategy": label_strategy,
        "features": FEATURE_COLS,
        "n_samples": len(frame),
        "n_high_risk": int(labels.sum()),
        "risk_f1": round(float(risk_f1), 4),
        "contamination": contamination,
    }
    (out_dir / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    ARTEFACTS_DIR.mkdir(parents=True, exist_ok=True)
    (ARTEFACTS_DIR / "latest.txt").write_text(version, encoding="utf-8")

    invalidate_cache()
    LOGGER.info("Saved version %s. risk_f1=%.3f", version, risk_f1)
    return meta


def main(argv: list[str]) -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    args = parse_args(argv)
    train_models(snapshot_id=args.snapshot, strategy=args.strategy)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
