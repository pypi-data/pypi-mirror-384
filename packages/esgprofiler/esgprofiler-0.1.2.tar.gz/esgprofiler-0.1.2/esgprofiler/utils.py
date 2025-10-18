"""Helper utilities for ESGProfiler."""
from typing import Any, Dict


def normalize_text(text: str) -> str:
    """Light normalization helper."""
    return " ".join(text.split())
