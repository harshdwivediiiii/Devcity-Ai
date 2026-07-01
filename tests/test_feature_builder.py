"""
Tests for src/ml/feature_builder.py

These tests verify that ``build_features`` correctly extracts, defaults, and
encodes features from raw per-file records.
"""

from typing import ClassVar

import pytest

from src.ml.feature_builder import build_features


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def make_record(**overrides) -> dict:
    """Return a minimal valid file record with optional field overrides."""
    base = {
        "size": 100,
        "complexity": 5.0,
        "depth": 2,
        "extension": ".py",
        "churn": 3,
        "comment_density": 0.2,
        "max_function_length": 30,
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Return type & keys
# ---------------------------------------------------------------------------

class TestBuildFeaturesReturnShape:
    """build_features must return a dict with the required keys."""

    REQUIRED_KEYS: ClassVar[set[str]] = {
        "size",
        "complexity",
        "depth",
        "type_importance",
        "churn",
        "comment_density",
        "max_function_length",
    }

    def test_returns_dict(self):
        result = build_features(make_record())
        assert isinstance(result, dict)

    def test_all_required_keys_present(self):
        result = build_features(make_record())
        assert self.REQUIRED_KEYS.issubset(result.keys())

    def test_all_values_are_floats(self):
        result = build_features(make_record())
        for key, value in result.items():
            assert isinstance(value, float), f"Key '{key}' is not a float: {value!r}"


# ---------------------------------------------------------------------------
# Type importance encoding
# ---------------------------------------------------------------------------

class TestTypeImportanceEncoding:
    """High-value source file extensions must get type_importance == 1.0."""

    @pytest.mark.parametrize("ext", [".py", ".js", ".ts", ".java", ".go", ".rs", ".cs", ".cpp"])
    def test_primary_source_extension_gets_full_weight(self, ext):
        result = build_features(make_record(extension=ext))
        assert result["type_importance"] == 1.0

    @pytest.mark.parametrize("ext", [".md", ".txt", ".yaml", ".json", ".css", ".png"])
    def test_non_source_extension_gets_low_weight(self, ext):
        result = build_features(make_record(extension=ext))
        assert result["type_importance"] == pytest.approx(0.1)

    def test_unknown_extension_gets_low_weight(self):
        result = build_features(make_record(extension=".xyzzy"))
        assert result["type_importance"] == pytest.approx(0.1)

    def test_extension_matching_is_case_insensitive(self):
        result = build_features(make_record(extension=".PY"))
        assert result["type_importance"] == 1.0


# ---------------------------------------------------------------------------
# Missing / None field handling
# ---------------------------------------------------------------------------

class TestMissingFieldDefaults:
    """Missing or None fields must be replaced with safe zero defaults."""

    def test_empty_record_does_not_raise(self):
        """build_features must tolerate a completely empty dict."""
        result = build_features({})
        assert result["size"] == 0.0
        assert result["complexity"] == pytest.approx(1.0)
        assert result["depth"] == 0.0
        assert result["type_importance"] == pytest.approx(0.1)
        assert result["churn"] == 0.0
        assert result["comment_density"] == 0.0
        assert result["max_function_length"] == 0.0

    def test_none_values_are_treated_as_zero(self):
        record = make_record(size=None, churn=None, max_function_length=None)
        result = build_features(record)
        assert result["size"] == 0.0
        assert result["churn"] == 0.0
        assert result["max_function_length"] == 0.0

    def test_none_comment_density_defaults_to_zero(self):
        record = make_record(comment_density=None)
        result = build_features(record)
        assert result["comment_density"] == 0.0


# ---------------------------------------------------------------------------
# Value passthrough
# ---------------------------------------------------------------------------

class TestValuePassthrough:
    """Values that need no transformation must be passed through unchanged."""

    def test_size_is_converted_to_float(self):
        result = build_features(make_record(size=250))
        assert result["size"] == pytest.approx(250.0)

    def test_complexity_is_passed_through(self):
        result = build_features(make_record(complexity=12.5))
        assert result["complexity"] == pytest.approx(12.5)

    def test_depth_is_converted_to_float(self):
        result = build_features(make_record(depth=3))
        assert result["depth"] == pytest.approx(3.0)

    def test_comment_density_is_passed_through(self):
        result = build_features(make_record(comment_density=0.45))
        assert result["comment_density"] == pytest.approx(0.45)

    def test_max_function_length_is_passed_through(self):
        result = build_features(make_record(max_function_length=75))
        assert result["max_function_length"] == pytest.approx(75.0)
