# ESG keyword lists — expand or tailor per use-case/industry for better accuracy
DEFAULT_ENVIRONMENT_KEYWORDS = [
    "emissions", "waste", "renewable", "pollution", "carbon", "energy efficiency",
    "sustainability", "climate", "recycle", "biodiversity", "water usage", "air quality"
]

DEFAULT_SOCIAL_KEYWORDS = [
    "diversity", "inclusion", "community", "donation", "charity", "well-being",
    "labor rights", "health and safety", "employee", "training", "equality", "volunteer"
]

DEFAULT_GOVERNANCE_KEYWORDS = [
    "board", "audit", "compliance", "transparency", "anti-corruption", "governance",
    "shareholder", "ethics", "whistleblower", "risk management", "disclosure"
]

# ESG scoring weights: Tuple (E, S, G)
DEFAULT_WEIGHTS = (0.33, 0.33, 0.34)

# Sector-based weights (adjust as needed)
SECTOR_WEIGHTS = {
    "energy":      (0.5, 0.25, 0.25),
    "financials":  (0.25, 0.25, 0.5),
    "healthcare":  (0.3, 0.5, 0.2)
}

def get_sector_weights(sector):
    """
    Return ESG weights for a given sector.
    """
    return SECTOR_WEIGHTS.get(sector.lower(), DEFAULT_WEIGHTS)

def get_default_keywords():
    return {
        "environment_keywords": DEFAULT_ENVIRONMENT_KEYWORDS,
        "social_keywords": DEFAULT_SOCIAL_KEYWORDS,
        "governance_keywords": DEFAULT_GOVERNANCE_KEYWORDS,
        "weights": DEFAULT_WEIGHTS,
    }
