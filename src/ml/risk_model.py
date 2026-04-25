def compute_risk_score(features: dict[str, float]) -> float:
    """
    Compute a lightweight risk score (0 to 1) based on combinations of features.
    No heavy dependencies, just algorithmic scoring representing an ML model.
    """
    # Roughly normalize features
    size_norm = min(features['size'] / 10000.0, 1.0)        # Assume 10,000 LOC is 100% size risk
    complexity_norm = min(features['complexity'] / 50.0, 1.0) # Assume McCabe 50 is 100% complexity risk
    churn_norm = min(features['churn'] / 20.0, 1.0)         # Assume 20 changes is high churn
    
    # Weights: Complexity (50%), Size (20%), Churn (20%), FileType (10%)
    raw_score = (
        0.50 * complexity_norm + 
        0.20 * size_norm +
        0.20 * churn_norm +
        0.10 * features['type_importance']
    )
    
    return round(min(raw_score, 1.0), 4)
