"""
Tests for src/ml/risk_model.py

These tests verify that ``compute_risk_score`` produces sensible, bounded,
and monotonic scores given various feature combinations.
"""

import pytest

from src.ml.risk_model import compute_risk_score


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def low_risk_features() -> dict:
    """A feature dict representing a clean, well-commented, simple file."""
    return {
        "complexity": 2.0,
        "size": 50.0,
        "churn": 1.0,
        "type_importance": 1.0,
        "comment_density": 0.6,      # 60 % of lines are comments
        "max_function_length": 15.0,
    }


def high_risk_features() -> dict:
    """A feature dict representing a large, complex, undocumented file."""
    return {
        "complexity": 80.0,          # very high cyclomatic complexity
        "size": 15_000.0,            # enormous file
        "churn": 50.0,               # extremely high churn
        "type_importance": 1.0,
        "comment_density": 0.0,      # zero comments
        "max_function_length": 500.0,
    }


# ---------------------------------------------------------------------------
# Bounds & type checks
# ---------------------------------------------------------------------------

class TestScoreBounds:
    """Risk score must always be a float in [0.0, 1.0]."""

    def test_score_is_float(self):
        score = compute_risk_score(low_risk_features())
        assert isinstance(score, float)

    def test_score_not_below_zero(self):
        score = compute_risk_score(low_risk_features())
        assert score >= 0.0

    def test_score_not_above_one(self):
        # Extreme values must be clamped
        score = compute_risk_score(high_risk_features())
        assert score <= 1.0

    def test_zero_features_produce_non_negative_score(self):
        all_zeros = {
            "complexity": 0.0,
            "size": 0.0,
            "churn": 0.0,
            "type_importance": 0.0,
            "comment_density": 0.0,
            "max_function_length": 0.0,
        }
        score = compute_risk_score(all_zeros)
        assert 0.0 <= score <= 1.0


# ---------------------------------------------------------------------------
# Relative ordering (monotonicity checks)
# ---------------------------------------------------------------------------

class TestScoreOrdering:
    """Higher-risk inputs must produce higher scores than lower-risk inputs."""

    def test_high_risk_exceeds_low_risk(self):
        low = compute_risk_score(low_risk_features())
        high = compute_risk_score(high_risk_features())
        assert high > low

    def test_increasing_complexity_increases_score(self):
        base = low_risk_features()
        low_c = compute_risk_score({**base, "complexity": 3.0})
        high_c = compute_risk_score({**base, "complexity": 40.0})
        assert high_c > low_c

    def test_increasing_size_increases_score(self):
        base = low_risk_features()
        small = compute_risk_score({**base, "size": 100.0})
        large = compute_risk_score({**base, "size": 9_000.0})
        assert large > small

    def test_increasing_churn_increases_score(self):
        base = low_risk_features()
        low_churn = compute_risk_score({**base, "churn": 1.0})
        high_churn = compute_risk_score({**base, "churn": 18.0})
        assert high_churn > low_churn

    def test_lower_comment_density_increases_score(self):
        """A file with no comments should score higher than a well-commented one."""
        base = low_risk_features()
        well_commented = compute_risk_score({**base, "comment_density": 0.5})
        undocumented = compute_risk_score({**base, "comment_density": 0.0})
        assert undocumented > well_commented

    def test_longer_max_function_increases_score(self):
        base = low_risk_features()
        short_fn = compute_risk_score({**base, "max_function_length": 10.0})
        long_fn = compute_risk_score({**base, "max_function_length": 180.0})
        assert long_fn > short_fn


# ---------------------------------------------------------------------------
# Missing field tolerance
# ---------------------------------------------------------------------------

class TestMissingFields:
    """compute_risk_score must not crash on sparse feature dicts."""

    def test_missing_comment_density_does_not_raise(self):
        features = {k: v for k, v in low_risk_features().items() if k != "comment_density"}
        score = compute_risk_score(features)
        assert 0.0 <= score <= 1.0

    def test_missing_max_function_length_does_not_raise(self):
        features = {k: v for k, v in low_risk_features().items() if k != "max_function_length"}
        score = compute_risk_score(features)
        assert 0.0 <= score <= 1.0


# ---------------------------------------------------------------------------
# Precision
# ---------------------------------------------------------------------------

class TestScorePrecision:
    """Scores must be rounded to four decimal places."""

    def test_score_has_at_most_four_decimal_places(self):
        score = compute_risk_score(low_risk_features())
        # Convert to string and check decimal places
        decimal_part = str(score).split(".")[-1] if "." in str(score) else ""
        assert len(decimal_part) <= 4
