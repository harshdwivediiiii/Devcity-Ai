"""
Anomaly detection engine for the DevCity AI ML pipeline.

Detects files that are statistical outliers across *multiple* metrics using a
Z-score approach.  Each detected anomaly is annotated with:

- ``score``      : a continuous value in [0.0, 1.0] (higher = more anomalous)
- ``confidence`` : how certain we are the file is a true outlier (0.0 – 1.0)
- ``reasons``    : human-readable list of explanations (Explainable AI)

This satisfies the project's "Explainable AI" architecture principle — every
ML recommendation includes confidence and reasoning.
"""

import math
from typing import Any


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _zscore_stats(values: list[float]) -> tuple[float, float]:
    """
    Compute the mean and standard deviation for a list of floats.

    Args:
        values: A non-empty list of numeric values.

    Returns:
        A ``(mean, std_dev)`` tuple.  ``std_dev`` is at least 1e-9 to avoid
        division by zero when all values are identical.
    """
    n = len(values)
    mean = sum(values) / n
    variance = sum((v - mean) ** 2 for v in values) / n
    std_dev = math.sqrt(variance) if variance > 0 else 1e-9
    return mean, std_dev


def _zscore(value: float, mean: float, std_dev: float) -> float:
    """
    Compute the absolute Z-score of a single value.

    The absolute Z-score measures how many standard deviations a value is
    away from the population mean — the larger the value, the more unusual.

    Args:
        value:   The observation to score.
        mean:    Population mean.
        std_dev: Population standard deviation (must be > 0).

    Returns:
        ``|value - mean| / std_dev``
    """
    return abs(value - mean) / std_dev


def _zscore_to_score(z: float, threshold: float = 2.0) -> float:
    """
    Convert a Z-score into a continuous anomaly score in [0.0, 1.0].

    Below ``threshold`` standard deviations → score 0.0 (normal).
    At ``threshold`` → score starts rising.
    At ``threshold * 2`` → score reaches ~1.0 (very anomalous).

    Using a sigmoid-like ramp instead of a hard 0/1 cutoff gives a smoother
    signal that the visualisation and downstream models can use.

    Args:
        z:         Absolute Z-score.
        threshold: The Z-score at which a value starts being flagged.

    Returns:
        A float in [0.0, 1.0].
    """
    if z <= threshold:
        return 0.0
    # Linear ramp from 0 at `threshold` to 1 at `threshold * 2`
    excess = z - threshold
    return round(min(excess / threshold, 1.0), 4)


def _confidence_from_zscore(z: float, threshold: float = 2.0) -> float:
    """
    Estimate detection confidence from a Z-score.

    Confidence rises with the distance of the value from the threshold.
    At exactly the threshold we have moderate confidence (0.5); it climbs
    slowly afterward (e.g. ~0.75 at 3x threshold) and only approaches 1.0
    asymptotically for much larger z values.

    Args:
        z:         Absolute Z-score.
        threshold: The detection threshold.

    Returns:
        A float in [0.0, 1.0].
    """
    if z < threshold:
        return 0.0
    # Sigmoid-style: confidence = z / (z + threshold).
    # At exactly z == threshold this yields 0.5 (boundary — moderate confidence).
    return round(min(z / (z + threshold), 1.0), 4)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def detect_anomalies(
    features_list: list[dict[str, Any]],
    z_threshold: float = 2.0,
) -> list[dict[str, Any]]:
    """
    Run multi-metric Z-score anomaly detection over a list of file feature dicts.

    Each file is evaluated against the population distribution for **four**
    metrics:

    1. ``complexity``           — average cyclomatic complexity
    2. ``size``                 — number of non-blank lines
    3. ``max_function_length``  — length of the longest function
    4. ``comment_density`` (inverted) — lack of comments is a risk signal

    The final anomaly ``score`` is the *maximum* single-metric score so that
    even a single extreme dimension flags the file.

    Args:
        features_list: List of feature dicts, one per file.  Each dict must
                       contain at least ``complexity``.  Other keys fall back
                       to 0.0 if absent.
        z_threshold:   Number of standard deviations beyond which a value is
                       considered anomalous.  Default is 2.0 (looser than the
                       traditional 3σ rule to catch moderate outliers early).

    Returns:
        A list of result dicts, one per input file, each containing:

        - ``score``      (float, 0.0 – 1.0) — overall anomaly severity
        - ``confidence`` (float, 0.0 – 1.0) — detection confidence
        - ``reasons``    (list[str])         — human-readable explanations

        An empty list is returned if ``features_list`` is empty.

    Example::

        results = detect_anomalies(features_list)
        for file_features, result in zip(features_list, results):
            print(result["score"], result["reasons"])
    """
    if not features_list:
        return []

    # --- Extract per-metric value arrays ------------------------------------
    complexities = [float(f.get("complexity") or 0.0) for f in features_list]
    sizes = [float(f.get("size") or 0.0) for f in features_list]
    fn_lengths = [float(f.get("max_function_length") or 0.0) for f in features_list]
    # Invert comment_density: a file with NO comments (0.0) is unusual if all
    # others have decent coverage; we detect the *absence* of comments.
    no_comment = [1.0 - float(f.get("comment_density") or 0.0) for f in features_list]

    # --- Compute population statistics per metric ---------------------------
    c_mean, c_std = _zscore_stats(complexities)
    s_mean, s_std = _zscore_stats(sizes)
    fn_mean, fn_std = _zscore_stats(fn_lengths)
    nc_mean, nc_std = _zscore_stats(no_comment)

    # --- Score each file ----------------------------------------------------
    results: list[dict[str, Any]] = []

    for i, features in enumerate(features_list):
        metric_scores: list[tuple[float, float, str]] = []
        # Each entry: (anomaly_score, z_score, human-readable reason)

        # 1. Cyclomatic complexity
        z_c = _zscore(complexities[i], c_mean, c_std)
        sc_c = _zscore_to_score(z_c, z_threshold)
        if sc_c > 0:
            metric_scores.append((
                sc_c,
                z_c,
                f"Complexity {complexities[i]:.1f} is {z_c:.1f}σ above the repo mean "
                f"({c_mean:.1f}). Highly complex code is harder to test and review.",
            ))

        # 2. File size (non-blank lines)
        z_s = _zscore(sizes[i], s_mean, s_std)
        sc_s = _zscore_to_score(z_s, z_threshold)
        if sc_s > 0:
            metric_scores.append((
                sc_s,
                z_s,
                f"File size {int(sizes[i])} lines is {z_s:.1f}σ above the repo mean "
                f"({s_mean:.0f} lines). Large files accumulate technical debt.",
            ))

        # 3. Max function length
        z_fn = _zscore(fn_lengths[i], fn_mean, fn_std)
        sc_fn = _zscore_to_score(z_fn, z_threshold)
        if sc_fn > 0:
            metric_scores.append((
                sc_fn,
                z_fn,
                f"Longest function is {int(fn_lengths[i])} lines ({z_fn:.1f}σ above "
                f"repo mean of {fn_mean:.0f} lines). Long functions are hard to unit-test.",
            ))

        # 4. Absence of comments
        z_nc = _zscore(no_comment[i], nc_mean, nc_std)
        sc_nc = _zscore_to_score(z_nc, z_threshold)
        if sc_nc > 0 and no_comment[i] > 0.9:
            # Only flag if comment_density is genuinely very low (<10 %)
            metric_scores.append((
                sc_nc,
                z_nc,
                f"Comment density {(1 - no_comment[i]) * 100:.0f}% is unusually low "
                f"({z_nc:.1f}σ below the repo mean). Under-documented code raises "
                "maintenance risk.",
            ))

        # --- Aggregate ----------------------------------------------------------
        if metric_scores:
            # Take the worst single-metric score as the overall anomaly score.
            # This means even one extreme dimension triggers the alert.
            best = max(metric_scores, key=lambda t: t[0])
            overall_score = best[0]
            # Confidence: average Z-score of flagged metrics → confidence formula
            avg_z = sum(t[1] for t in metric_scores) / len(metric_scores)
            confidence = _confidence_from_zscore(avg_z, z_threshold)
            reasons = [t[2] for t in metric_scores]
        else:
            overall_score = 0.0
            confidence = 0.0
            reasons = []

        results.append({
            "score": overall_score,
            "confidence": confidence,
            "reasons": reasons,
        })

    return results
