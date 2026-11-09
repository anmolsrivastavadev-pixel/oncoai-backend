"""CV-only analyzer used when no model checkpoint is available."""

from __future__ import annotations

from PIL import Image

from app.ml.analyzer import AnalysisResult, ModelInfo, to_rgb_array
from app.ml.cv_features import analyze_image

HEURISTIC_VERSION = "cv-abcde-1.0"


class HeuristicAnalyzer:
    def __init__(self) -> None:
        self._info = ModelInfo(
            name="OncoAI visual-pattern heuristics", kind="heuristic", version=HEURISTIC_VERSION, loaded=True
        )

    @property
    def info(self) -> ModelInfo:
        return self._info

    def analyze(self, image: Image.Image) -> AnalysisResult:
        return AnalysisResult(cv=analyze_image(to_rgb_array(image)), info=self._info)
