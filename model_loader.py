import json
import logging
from pathlib import Path
from typing import Any

import joblib


LOGGER = logging.getLogger(__name__)
MODELS_DIR = Path(__file__).resolve().parent / "models" / "artefacts"
_cache: dict[str, Any] = {}


def load_models() -> tuple[tuple[Any, Any] | None, Any | None]:
    """
    Returns ``(risk_model, anomaly_model)`` loaded from the active artefact version.
    """
    if "loaded" in _cache:
        return _cache["risk"], _cache["anomaly"]

    latest_file = MODELS_DIR / "latest.txt"
    if not latest_file.exists():
        LOGGER.warning("model_loader: no latest.txt - scores will be null")
        _cache["loaded"] = True
        _cache["risk"] = None
        _cache["anomaly"] = None
        return None, None

    version = latest_file.read_text(encoding="utf-8").strip()
    version_dir = MODELS_DIR / version

    try:
        risk = joblib.load(version_dir / "risk_model.joblib")
        anomaly = joblib.load(version_dir / "anomaly_model.joblib")
        LOGGER.info("model_loader: loaded version %s", version)
    except Exception as error:
        LOGGER.error("model_loader: failed to load models - %s", error)
        risk, anomaly = None, None

    _cache["loaded"] = True
    _cache["risk"] = risk
    _cache["anomaly"] = anomaly
    return risk, anomaly


def get_model_meta() -> dict[str, Any] | None:
    """Return ``meta.json`` for the current active model version, if present."""
    latest_file = MODELS_DIR / "latest.txt"
    if not latest_file.exists():
        return None

    version = latest_file.read_text(encoding="utf-8").strip()
    meta_path = MODELS_DIR / version / "meta.json"
    if meta_path.exists():
        return json.loads(meta_path.read_text(encoding="utf-8"))
    return None


def invalidate_cache() -> None:
    """Clear the in-process model cache."""
    _cache.clear()
