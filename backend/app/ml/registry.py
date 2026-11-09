"""Process-wide analyzer selection: a single, lazily created instance."""

from __future__ import annotations

import logging
import threading

from PIL import Image

from app.core.config import settings
from app.ml.analyzer import Analyzer
from app.ml.heuristic_analyzer import HeuristicAnalyzer
from app.ml.vit_analyzer import ModelLoadError, ViTAnalyzer

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_analyzer: Analyzer | None = None


def _build() -> Analyzer:
    if settings.ANALYZER_KIND == "heuristic":
        return HeuristicAnalyzer()
    try:
        return ViTAnalyzer(settings.MODEL_DIR, settings.MODEL_LABEL_WEIGHTS, settings.MODEL_DISPLAY_NAME)
    except ModelLoadError as exc:
        level = logging.ERROR if settings.ANALYZER_KIND == "vit" else logging.WARNING
        logger.log(level, "falling back to heuristic analyzer: %s", exc)
    except Exception:  # corrupt checkpoint, incompatible transformers version, ...
        logger.exception("model failed to load; falling back to heuristic analyzer")
    return HeuristicAnalyzer()


def get_analyzer() -> Analyzer:
    global _analyzer
    if _analyzer is None:
        with _lock:
            if _analyzer is None:
                _analyzer = _build()
    return _analyzer


def reset_analyzer() -> None:
    """Drop the cached instance (used by tests and after swapping checkpoints)."""
    global _analyzer
    with _lock:
        _analyzer = None


def warmup() -> None:
    analyzer = get_analyzer()
    analyzer.analyze(Image.new("RGB", (64, 64), (200, 160, 140)))
    logger.info("analyzer ready", extra={"kind": analyzer.info.kind, "model": analyzer.info.name})
