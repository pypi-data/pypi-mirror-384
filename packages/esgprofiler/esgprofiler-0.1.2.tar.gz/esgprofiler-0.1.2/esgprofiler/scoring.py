import numpy as np

def aggregate_esg_counts(counts):
    """
    Aggregate raw keyword hit counts to normalized ESG subscores (0-100 scale).
    """
    # Example normalization: scale by max of observed counts (customize per data or config.py)
    env_score = min(counts["environment"], 50) * 2  # Cap at 100
    soc_score = min(counts["social"], 50) * 2
    gov_score = min(counts["governance"], 50) * 2
    return {
        "environment_score": env_score,
        "social_score": soc_score,
        "governance_score": gov_score
    }

def compute_overall_esg_score(subscores, weights=(0.33, 0.33, 0.34)):
    """
    Weighted average of E/S/G subscores to get overall ESG score.
    Can tune weights per sector in config.py.
    """
    env = subscores.get("environment_score", 0)
    soc = subscores.get("social_score", 0)
    gov = subscores.get("governance_score", 0)
    overall = weights[0] * env + weights[1] * soc + weights[2] * gov
    return round(overall, 2)

def score_esg_text(text, config=None):
    """
    Full pipeline—count mentions, aggregate subscores, return composite.
    Optionally provide config (keywords, weights).
    """
    from .nlp_extract import count_esg_mentions
    if config:
        counts = count_esg_mentions(
            text,
            config.get("environment_keywords"),
            config.get("social_keywords"),
            config.get("governance_keywords"),
        )
        weights = config.get("weights", (0.33, 0.33, 0.34))
    else:
        counts = count_esg_mentions(text)
        weights = (0.33, 0.33, 0.34)
    subscores = aggregate_esg_counts(counts)
    overall = compute_overall_esg_score(subscores, weights)
    results = subscores.copy()
    results["overall_score"] = overall
    return results
