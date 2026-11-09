"""Hugging Face image-classifier analyzer (ViT by default), CPU inference.

The checkpoint is loaded from a local directory (``settings.MODEL_DIR``); nothing is
downloaded at runtime. Use ``scripts/fetch_model.py`` to populate the directory.
"""

from __future__ import annotations

import hashlib
import logging
import threading
from pathlib import Path
from typing import Any

from PIL import Image

from app.ml.analyzer import AnalysisResult, ModelInfo, to_rgb_array
from app.ml.cv_features import analyze_image
from app.ml.labels import pattern_risk_score, resolve_label_weights

logger = logging.getLogger(__name__)


class ModelLoadError(RuntimeError):
    pass


def checkpoint_present(model_dir: Path) -> bool:
    return (model_dir / "config.json").is_file() and any(
        (model_dir / name).is_file() for name in ("model.safetensors", "pytorch_model.bin")
    )


def _fingerprint(model_dir: Path) -> str:
    digest = hashlib.sha256((model_dir / "config.json").read_bytes())
    for name in ("model.safetensors", "pytorch_model.bin"):
        path = model_dir / name
        if path.is_file():
            stat = path.stat()
            digest.update(f"{name}:{stat.st_size}".encode())
    return digest.hexdigest()[:12]


class ViTAnalyzer:
    def __init__(self, model_dir: Path, label_weights: dict[str, float], display_name: str) -> None:
        if not checkpoint_present(model_dir):
            raise ModelLoadError(f"No model checkpoint found in {model_dir}")
        try:
            import torch
            from transformers import AutoImageProcessor, AutoModelForImageClassification
        except ImportError as exc:  # pragma: no cover - depends on installed extras
            raise ModelLoadError("torch/transformers are not installed") from exc

        self._torch = torch
        self._processor: Any = AutoImageProcessor.from_pretrained(model_dir)
        self._model: Any = AutoModelForImageClassification.from_pretrained(model_dir)
        self._model.eval()
        self._model.to("cpu")
        self._lock = threading.Lock()

        id2label = {int(k): str(v) for k, v in self._model.config.id2label.items()}
        self._labels = [id2label[i] for i in sorted(id2label)]
        self._index_weights = resolve_label_weights(id2label, label_weights)
        if not any(w > 0 for w in self._index_weights.values()):
            raise ModelLoadError(
                "None of the configured MODEL_LABEL_WEIGHTS keys match the checkpoint's "
                f"labels; refusing to use a model whose risk score would always be 0. "
                f"Labels: {self._labels}"
            )
        self._info = ModelInfo(
            name=display_name, kind="vit", version=_fingerprint(model_dir), loaded=True
        )
        logger.info(
            "image classifier loaded",
            extra={"model_dir": str(model_dir), "num_labels": len(self._labels)},
        )

    @property
    def info(self) -> ModelInfo:
        return self._info

    def predict_probabilities(self, image: Image.Image) -> list[float]:
        inputs = self._processor(images=image.convert("RGB"), return_tensors="pt")
        # The module isn't re-entrant-safe for set_num_threads etc.; inference itself is
        # cheap enough on CPU that serialising calls avoids oversubscription.
        with self._lock, self._torch.inference_mode():
            logits = self._model(**inputs).logits
            probs = self._torch.softmax(logits, dim=-1)[0]
        return [float(p) for p in probs.tolist()]

    def analyze(self, image: Image.Image) -> AnalysisResult:
        cv = analyze_image(to_rgb_array(image))
        probs = self.predict_probabilities(image)
        probabilities = {label: round(p, 6) for label, p in zip(self._labels, probs, strict=True)}
        score = pattern_risk_score(probs, self._index_weights)
        logger.debug("model probabilities", extra={"probabilities": probabilities, "score": score})
        return AnalysisResult(cv=cv, info=self._info, model_score=score, probabilities=probabilities)
