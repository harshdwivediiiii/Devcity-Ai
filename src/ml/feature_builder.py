"""
Feature builder for the DevCity AI ML pipeline.

Converts raw per-file records (produced by ``scanner2.analyze_file``) into a
flat feature dict suitable for risk scoring and anomaly detection.
"""

from typing import Any


def build_features(record: dict[str, Any]) -> dict[str, float]:
    """
    Extract ML-ready numerical features from a per-file record.

    Each feature is guaranteed to be a float.  Missing fields are replaced
    with safe zero/default values so downstream models never receive ``None``.

    Feature descriptions
    --------------------
    size
        Number of non-blank lines in the file.  A rough proxy for how much
        logic the file contains.

    complexity
        Average cyclomatic complexity across all functions in the file.
        Higher values indicate more branching paths and harder-to-test code.

    depth
        Directory nesting level (number of ``/`` characters in the file
        path).  Very deeply nested files can signal poor module organisation.

    type_importance
        A weight that encodes how "critical" a file extension is.  Source
        files in primary languages (.py, .js, .ts, …) receive 1.0; all other
        extensions (configs, assets, …) receive 0.1.

    churn
        Total number of git commits that touched this file.  High churn often
        correlates with instability or ongoing refactors.

    comment_density
        Fraction of non-blank lines that are comment lines (0.0 - 1.0).  A
        file with almost no comments is harder to maintain and review.

    max_function_length
        Number of lines in the longest function inside the file.  Very long
        functions are difficult to unit-test and are a common source of bugs.

    Args:
        record: A dict produced by ``scanner2.analyze_file`` (or any dict
                containing the expected keys).

    Returns:
        A flat dict mapping feature name → float value.
    """
    size = float(record.get("size") or 0)
    complexity = float(record.get("complexity") or 1.0)
    depth = float(record.get("depth") or 0)
    extension = str(record.get("extension") or "")
    churn = float(record.get("churn") or 0.0)
    comment_density = float(record.get("comment_density") or 0.0)
    max_function_length = float(record.get("max_function_length") or 0.0)

    # Higher weight for backend/logic files; low weight for configs, docs, etc.
    important_types = {
        ".py": 1.0,
        ".js": 1.0,
        ".ts": 1.0,
        ".java": 1.0,
        ".cpp": 1.0,
        ".go": 1.0,
        ".rs": 1.0,
        ".cs": 1.0,
    }
    type_importance = important_types.get(extension.lower(), 0.1)

    return {
        "size": size,
        "complexity": complexity,
        "depth": depth,
        "type_importance": type_importance,
        "churn": churn,
        "comment_density": comment_density,
        "max_function_length": max_function_length,
    }
