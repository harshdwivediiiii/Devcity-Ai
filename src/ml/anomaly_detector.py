import math

def detect_anomalies(features_list: list[dict[str, float]]) -> list[float]:
    """
    Simple Z-score based anomaly detection over the complexities of files.
    Returns anomaly_score (0 or 1).
    """
    if not features_list:
        return []
        
    complexities = [f['complexity'] for f in features_list]
    mean = sum(complexities) / len(complexities)
    variance = sum((c - mean) ** 2 for c in complexities) / len(complexities)
    std_dev = math.sqrt(variance) if variance > 0 else 1.0
    
    anomaly_scores = []
    for c in complexities:
        z_score = abs(c - mean) / std_dev
        # Flag as anomaly (1.0) if z_score > 3 (3 standard deviations from mean)
        score = 1.0 if z_score > 3.0 else 0.0
        anomaly_scores.append(score)
        
    return anomaly_scores
