import json
import logging
from pathlib import Path
from typing import Any

import squarify

from db import bulk_insert_file_metrics, db_init, insert_snapshot, update_snapshot_file_count
from model_loader import get_model_meta, load_models
from scanner2 import build_city_from_github


LOGGER = logging.getLogger(__name__)
BASE_DIR = Path(__file__).resolve().parent.parent
SNAPSHOT_DIR = BASE_DIR / "snapshots"
CURRENT_DATA_PATH = BASE_DIR / "city_data2.json"
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


def _complexity_color(complexity: float) -> str:
    if complexity <= 5:
        return "#00ffcc"
    if complexity <= 15:
        return "#00ff88"
    if complexity <= 30:
        return "#FFC300"
    if complexity <= 50:
        return "#ff9900"
    return "#ff4444"


def _ensure_record_defaults(record: dict[str, Any]) -> dict[str, Any]:
    enriched = dict(record)
    enriched.setdefault("name", "")
    enriched.setdefault("path", enriched.get("name", ""))
    enriched.setdefault("extension", "")
    enriched.setdefault("size", 0)
    enriched.setdefault("byte_size", 0)
    enriched.setdefault("complexity", 1.0)
    enriched.setdefault("function_count", 0)
    enriched.setdefault("avg_params", 0.0)
    enriched.setdefault("depth", 0)
    enriched.setdefault("churn", 0)
    enriched.setdefault("bug_churn", 0)
    enriched.setdefault("fan_out", 0)
    enriched.setdefault("risk_score", None)
    enriched.setdefault("anomaly_score", None)
    return enriched


def _apply_city_layout(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not records:
        return []

    normalized_records = [_ensure_record_defaults(record) for record in records]
    dynamic_area = max(150, int((len(normalized_records) ** 0.5) * 45))
    sizes = [max(int(record.get("size", 0)), 1) for record in normalized_records]
    if sum(sizes) == 0:
        sizes = [1] * len(normalized_records)

    values = squarify.normalize_sizes(sizes, dynamic_area, dynamic_area)
    rects = squarify.squarify(values, 0, 0, dynamic_area, dynamic_area)

    city_data: list[dict[str, Any]] = []
    for index, record in enumerate(normalized_records):
        complexity = float(record.get("complexity") or 1.0)
        city_record = dict(record)
        city_record.update(
            {
                "x": rects[index]["x"],
                "y": rects[index]["y"],
                "w": rects[index]["dx"],
                "d": rects[index]["dy"],
                "h": max(1.0, complexity * 2.0),
                "color": _complexity_color(complexity),
            }
        )
        city_data.append(city_record)
    return city_data


from src.ml.feature_builder import build_features
from src.ml.risk_model import compute_risk_score
from src.ml.anomaly_detector import detect_anomalies

def score_files(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Attach ``risk_score`` and ``anomaly_score`` to each record.
    Leverages ML feature engineering, risk scoring, and anomaly detection layers.
    """
    if not records:
        return records

    # 1. Feature Engineering Layer
    features_list = [build_features(record) for record in records]

    # 2. Anomaly Detection Layer (Batch calculation over all items)
    anomaly_scores = detect_anomalies(features_list)

    # 3. Attach scores
    for i, record in enumerate(records):
        features = features_list[i]
        
        # Calculate Risk Score from ML Risk Model
        record["risk_score"] = compute_risk_score(features)
        
        # Attach Anomaly Score
        record["anomaly_score"] = anomaly_scores[i]

    return records


def _write_snapshot_json(snapshot_meta: dict[str, Any], city_data: list[dict[str, Any]]) -> None:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    payload = {"meta": snapshot_meta, "data": city_data}
    snapshot_path = SNAPSHOT_DIR / f"{snapshot_meta['id']}.json"
    snapshot_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_current_city_data(city_data: list[dict[str, Any]]) -> None:
    CURRENT_DATA_PATH.write_text(json.dumps(city_data, indent=2), encoding="utf-8")


def analyze_and_store(
    repo_url: str,
    label: str,
    snapshot_meta: dict[str, Any],
    github_token: str | None = None,
) -> list[dict[str, Any]]:
    """
    Clone, scan, score, lay out, and persist a repository analysis snapshot.
    """
    raw_records = build_city_from_github(repo_url, github_token)
    scored_records = score_files(raw_records)
    city_data = _apply_city_layout(scored_records)

    model_meta = get_model_meta()
    snapshot_meta["repo_url"] = repo_url
    snapshot_meta["label"] = label or str(snapshot_meta.get("label") or repo_url)
    snapshot_meta["file_count"] = len(city_data)
    snapshot_meta["model_version"] = model_meta.get("version") if model_meta else None

    _write_current_city_data(city_data)
    _write_snapshot_json(snapshot_meta, city_data)

    try:
        db_init()
        insert_snapshot(snapshot_meta)
        bulk_insert_file_metrics(str(snapshot_meta["id"]), city_data)
        update_snapshot_file_count(str(snapshot_meta["id"]), len(city_data))
    except Exception:
        LOGGER.warning(
            "[PRO] SQLite persistence failed for snapshot %s",
            snapshot_meta.get("id"),
            exc_info=True,
        )

    return city_data
