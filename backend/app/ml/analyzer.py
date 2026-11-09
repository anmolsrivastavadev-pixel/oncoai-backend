"""Analyzer interface shared by the ViT and the heuristic (CV-only) implementations."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Protocol

import numpy as np
from PIL import Image

from app.ml.cv_features import CVAnalysis

AnalyzerKind = Literal["vit", "heuristic"]


@dataclass(frozen=True)
class ModelInfo:
    name: str
    kind: AnalyzerKind
    version: str
    loaded: bool


@dataclass(frozen=True)
class AnalysisResult:
    cv: CVAnalysis
    info: ModelInfo
    # Internal 0-100 "pattern-risk" score derived from model probabilities (ViT only).
    model_score: float | None = None
    # Raw class probabilities. INTERNAL ONLY: never serialised into API responses.
    probabilities: dict[str, float] = field(default_factory=dict)


class Analyzer(Protocol):
    @property
    def info(self) -> ModelInfo: ...

    def analyze(self, image: Image.Image) -> AnalysisResult: ...


def to_rgb_array(image: Image.Image) -> np.ndarray:
    return np.asarray(image.convert("RGB"), dtype=np.uint8)
