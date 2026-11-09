"""Mapping from model class labels to internal pattern-risk weights."""

from __future__ import annotations

import re


def normalize_label(label: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", label.strip().lower()).strip("_")


def resolve_label_weights(id2label: dict[int, str], weights: dict[str, float]) -> dict[int, float]:
    """Return {class_index: weight} for labels that match a configured weight key.

    Matching is case-insensitive and ignores punctuation/spacing differences, so
    "Basal Cell Carcinoma", "basal-cell-carcinoma" and "basal_cell_carcinoma" are equal.
    Unmatched labels get weight 0.
    """
    normalized = {normalize_label(key): float(value) for key, value in weights.items()}
    resolved: dict[int, float] = {}
    for index, label in id2label.items():
        weight = normalized.get(normalize_label(label))
        if weight is not None:
            resolved[int(index)] = weight
    return resolved


def pattern_risk_score(probabilities: list[float], index_weights: dict[int, float]) -> float:
    """Weighted sum of class probabilities, scaled to 0-100."""
    total = sum(probabilities[i] * w for i, w in index_weights.items() if i < len(probabilities))
    return round(min(100.0, max(0.0, total * 100.0)), 1)
