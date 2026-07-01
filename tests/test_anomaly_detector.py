"""
Tests for src/ml/anomaly_detector.py

These tests verify the multi-metric Z-score anomaly detector:

- Correct return shape and types
- Empty input handling
- Outlier detection (a file that is extreme in one metric must be flagged)
- Confidence and reasons are meaningful
- Normal (non-outlier) files produce score == 0.0
"""

import math

import pytest

from src.ml.anomaly_detector import (
    detect_anomalies,
    _zscore_stats,
    _zscore,
    _zscore_to_score,
    _confidence_from_zscore,
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

class TestZscoreStats:
    def test_returns_mean_and_std(self):
        mean, std = _zscore_stats([1.0, 2.0, 3.0, 4.0, 5.0])
        assert mean == pytest.approx(3.0)
        assert std == pytest.approx(math.sqrt(2.0), rel=1e-3)

    def test_identical_values_give_tiny_std(self):
        """All-identical list must not produce std == 0 (avoid ZeroDivisionError)."""
        _, std = _zscore_stats([7.0, 7.0, 7.0])
        assert std > 0

    def test_single_element(self):
        mean, std = _zscore_stats([42.0])
        assert mean == pytest.approx(42.0)
        assert std > 0  # fallback to 1e-9


class TestZscore:
    def test_same_as_mean_gives_zero(self):
        assert _zscore(3.0, 3.0, 1.0) == pytest.approx(0.0)

    def test_one_std_away(self):
        assert _zscore(4.0, 3.0, 1.0) == pytest.approx(1.0)

    def test_negative_deviation_is_absolute(self):
        assert _zscore(1.0, 3.0, 1.0) == pytest.approx(2.0)


class TestZscoreToScore:
    def test_below_threshold_returns_zero(self):
        assert _zscore_to_score(1.5, threshold=2.0) == pytest.approx(0.0)

    def test_at_threshold_returns_zero(self):
        assert _zscore_to_score(2.0, threshold=2.0) == pytest.approx(0.0)

    def test_double_threshold_returns_one(self):
        assert _zscore_to_score(4.0, threshold=2.0) == pytest.approx(1.0)

    def test_between_threshold_and_double(self):
        score = _zscore_to_score(3.0, threshold=2.0)
        assert 0.0 < score < 1.0


class TestConfidenceFromZscore:
    def test_below_threshold_gives_zero_confidence(self):
        assert _confidence_from_zscore(1.0, threshold=2.0) == pytest.approx(0.0)

    def test_at_threshold_gives_half_confidence(self):
        conf = _confidence_from_zscore(2.0, threshold=2.0)
        assert conf == pytest.approx(0.5)

    def test_confidence_increases_with_z(self):
        low = _confidence_from_zscore(2.5, threshold=2.0)
        high = _confidence_from_zscore(5.0, threshold=2.0)
        assert high > low

    def test_confidence_never_exceeds_one(self):
        conf = _confidence_from_zscore(1000.0, threshold=2.0)
        assert conf <= 1.0


# ---------------------------------------------------------------------------
# detect_anomalies — edge cases
# ---------------------------------------------------------------------------

class TestDetectAnomaliesEdgeCases:

    def test_empty_list_returns_empty_list(self):
        assert detect_anomalies([]) == []

    def test_single_file_does_not_raise(self):
        result = detect_anomalies([{"complexity": 5.0}])
        assert len(result) == 1

    def test_returns_list_of_same_length(self):
        files = [{"complexity": float(i)} for i in range(10)]
        result = detect_anomalies(files)
        assert len(result) == 10

    def test_result_dicts_have_required_keys(self):
        files = [{"complexity": 1.0}, {"complexity": 2.0}]
        results = detect_anomalies(files)
        for r in results:
            assert "score" in r
            assert "confidence" in r
            assert "reasons" in r

    def test_score_is_float_in_range(self):
        files = [{"complexity": float(i * 10)} for i in range(5)]
        for r in detect_anomalies(files):
            assert isinstance(r["score"], float)
            assert 0.0 <= r["score"] <= 1.0

    def test_confidence_is_float_in_range(self):
        files = [{"complexity": float(i * 10)} for i in range(5)]
        for r in detect_anomalies(files):
            assert isinstance(r["confidence"], float)
            assert 0.0 <= r["confidence"] <= 1.0

    def test_reasons_is_list_of_strings(self):
        files = [{"complexity": float(i)} for i in range(5)]
        for r in detect_anomalies(files):
            assert isinstance(r["reasons"], list)
            for reason in r["reasons"]:
                assert isinstance(reason, str)


# ---------------------------------------------------------------------------
# detect_anomalies — outlier detection
# ---------------------------------------------------------------------------

def _normal_files(n: int = 20, base_complexity: float = 5.0) -> list[dict]:
    """Create a list of similar files with low, uniform complexity."""
    return [
        {
            "complexity": base_complexity,
            "size": 100.0,
            "max_function_length": 20.0,
            "comment_density": 0.3,
        }
        for _ in range(n)
    ]


class TestDetectAnomaliesOutliers:

    def test_normal_files_score_zero(self):
        """Identical files have no variance so no file is anomalous."""
        results = detect_anomalies(_normal_files())
        for r in results:
            assert r["score"] == pytest.approx(0.0)

    def test_complexity_outlier_is_detected(self):
        """A file with extremely high complexity must get a non-zero score."""
        files = _normal_files(20)
        # Insert one extreme outlier at position 0
        files[0]["complexity"] = 1_000.0
        results = detect_anomalies(files)
        assert results[0]["score"] > 0.0, "Complexity outlier was not flagged"

    def test_size_outlier_is_detected(self):
        """A file with an unusually large line count must be flagged."""
        files = _normal_files(20)
        files[0]["size"] = 50_000.0
        results = detect_anomalies(files)
        assert results[0]["score"] > 0.0

    def test_max_function_length_outlier_is_detected(self):
        """A file with an abnormally long function must be flagged."""
        files = _normal_files(20)
        files[0]["max_function_length"] = 5_000.0
        results = detect_anomalies(files)
        assert results[0]["score"] > 0.0

    def test_outlier_has_non_empty_reasons(self):
        """Flagged files must provide at least one human-readable reason."""
        files = _normal_files(20)
        files[0]["complexity"] = 1_000.0
        results = detect_anomalies(files)
        assert len(results[0]["reasons"]) > 0

    def test_non_outlier_files_have_empty_reasons(self):
        """Normal files must have no reasons (nothing to explain)."""
        files = _normal_files(20)
        files[0]["complexity"] = 1_000.0  # outlier
        results = detect_anomalies(files)
        # All non-outlier files should have no reasons
        for i, r in enumerate(results[1:], start=1):
            assert r["reasons"] == [], f"File {i} unexpectedly has reasons: {r['reasons']}"

    def test_outlier_score_exceeds_normal_score(self):
        files = _normal_files(20)
        files[0]["complexity"] = 1_000.0
        results = detect_anomalies(files)
        max_normal_score = max(r["score"] for r in results[1:])
        assert results[0]["score"] > max_normal_score

    def test_outlier_confidence_is_above_zero(self):
        files = _normal_files(20)
        files[0]["complexity"] = 1_000.0
        results = detect_anomalies(files)
        assert results[0]["confidence"] > 0.0

    def test_custom_z_threshold(self):
        """A tighter threshold (1.5σ) should flag more files than the default (2.0σ)."""
        files = [{"complexity": float(i)} for i in range(1, 21)]
        tight_results = detect_anomalies(files, z_threshold=1.5)
        default_results = detect_anomalies(files, z_threshold=2.0)
        tight_flagged = sum(1 for r in tight_results if r["score"] > 0)
        default_flagged = sum(1 for r in default_results if r["score"] > 0)
        # Tighter threshold must flag at least as many files
        assert tight_flagged >= default_flagged
