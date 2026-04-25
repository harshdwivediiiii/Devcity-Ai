from typing import Any

def build_features(record: dict[str, Any]) -> dict[str, float]:
    """
    Extracts features from a file record for ML scoring.
    """
    size = float(record.get('size') or 0)
    complexity = float(record.get('complexity') or 1.0)
    depth = float(record.get('depth') or 0)
    extension = str(record.get('extension') or '')
    churn = float(record.get('churn') or 0.0)
    
    # Simple type encoding: higher weight for backend/logical code files
    important_types = {
        '.py': 1.0, '.js': 1.0, '.ts': 1.0, '.java': 1.0, 
        '.cpp': 1.0, '.go': 1.0, '.rs': 1.0, '.cs': 1.0
    }
    type_importance = important_types.get(extension.lower(), 0.1)
    
    return {
        "size": size,
        "complexity": complexity,
        "depth": depth,
        "type_importance": type_importance,
        "churn": churn
    }
