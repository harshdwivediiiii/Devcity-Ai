"""
Risk scoring model for the DevCity AI ML pipeline.

Computes a lightweight, interpretable risk score (0.0 – 1.0) for each file
based on a weighted combination of normalised feature values.  This is an
algorithmic model — it requires no trained weights file and runs instantly.

Score interpretation
--------------------
0.0 – 0.25  Low risk      (green in the city visualisation)
0.25 – 0.50 Moderate risk (yellow)
0.50 – 0.75 High risk     (orange)
0.75 – 1.0  Critical risk (red)
"""


# ---------------------------------------------------------------------------
# Normalisation thresholds
# ---------------------------------------------------------------------------
# These are the values at which each feature is considered "100 % risky".
# They were chosen from empirical observation of typical open-source repos.
_COMPLEXITY_CEILING = 50.0   # Average McCabe cyclomatic complexity
_SIZE_CEILING = 10_000.0     # Lines of code
_CHURN_CEILING = 20.0        # Git commit count
_MAX_FN_LEN_CEILING = 200.0  # Lines in the longest function


def compute_risk_score(features: dict[str, float]) -> float:
    """
    Compute a normalised risk score (0.0 – 1.0) for a single file.

    The score is a weighted sum of six normalised sub-scores.  All inputs
    are clamped to [0, 1] before weighting so the total can never exceed 1.

    Weight breakdown
    ----------------
    +-----------------------+--------+------------------------------------------+
    | Feature               | Weight | Rationale                                |
    +=======================+========+==========================================+
    | complexity            |  0.35  | Most reliable predictor of defect density|
    | comment_density (inv) |  0.20  | Low comments → harder to maintain/review |
    | size                  |  0.15  | Larger files tend to accumulate debt     |
    | max_function_length   |  0.15  | Long functions are hard to test          |
    | churn                 |  0.10  | Frequent changes signal instability      |
    | type_importance       |  0.05  | Source files matter more than configs    |
    +-----------------------+--------+-----------------------------------------+

    ``comment_density`` is *inverted* (1 - density) because a file with lots
    of comments is *less* risky, not more.

    Args:
        features: A dict produced by ``feature_builder.build_features``.

    Returns:
        A float in [0.0, 1.0] rounded to four decimal places.
    """
    # --- Normalise each feature to [0, 1] -----------------------------------
    # Clamp both ends: negative inputs (e.g. malformed records) are floored at
    # 0.0, and values above the ceiling are capped at 1.0.
    complexity_norm = max(0.0, min(features.get("complexity", 1.0) / _COMPLEXITY_CEILING, 1.0))
    size_norm = max(0.0, min(features.get("size", 0.0) / _SIZE_CEILING, 1.0))
    churn_norm = max(0.0, min(features.get("churn", 0.0) / _CHURN_CEILING, 1.0))
    max_fn_len_norm = max(0.0, min(features.get("max_function_length", 0.0) / _MAX_FN_LEN_CEILING, 1.0))

    # Invert comment_density: 0 comments → full risk contribution (1.0);
    # fully commented file → no risk contribution (0.0).
    comment_risk = 1.0 - max(0.0, min(features.get("comment_density", 0.0), 1.0))

    type_importance = max(0.0, min(features.get("type_importance", 0.1), 1.0))

    # --- Weighted combination -----------------------------------------------
    raw_score = (
        0.35 * complexity_norm
        + 0.20 * comment_risk
        + 0.15 * size_norm
        + 0.15 * max_fn_len_norm
        + 0.10 * churn_norm
        + 0.05 * type_importance
    )

    return round(max(0.0, min(raw_score, 1.0)), 4)
