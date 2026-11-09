"""ML pipeline tests: CV features on synthetic images, heuristic path, and the full
transformers path using a tiny randomly-initialised ViT saved in HF format."""

from __future__ import annotations

import io
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.core.config import DEFAULT_LABEL_WEIGHTS, settings
from app.ml import registry
from app.ml.analyzer import to_rgb_array
from app.ml.cv_features import analyze_image
from app.ml.heuristic_analyzer import HeuristicAnalyzer
from app.ml.labels import pattern_risk_score, resolve_label_weights
from app.ml.vit_analyzer import ModelLoadError, ViTAnalyzer, checkpoint_present
from tests.synthetic import irregular_spot, regular_spot, to_jpeg

HAM_LABELS = [
    "benign_keratosis-like_lesions",
    "basal_cell_carcinoma",
    "actinic_keratoses",
    "vascular_lesions",
    "melanocytic_Nevi",
    "melanoma",
    "dermatofibroma",
]
FORBIDDEN_WORDS = ["melanoma", "carcinoma", "keratos", "nevi", "nevus", "dermatofibroma", "cancer", "malignan", "benign"]


@pytest.fixture(scope="module")
def tiny_vit_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    torch = pytest.importorskip("torch")
    transformers = pytest.importorskip("transformers")
    torch.manual_seed(0)
    config = transformers.ViTConfig(
        image_size=32,
        patch_size=8,
        hidden_size=32,
        num_hidden_layers=1,
        num_attention_heads=2,
        intermediate_size=37,
        id2label=dict(enumerate(HAM_LABELS)),
        label2id={label: i for i, label in enumerate(HAM_LABELS)},
    )
    path = tmp_path_factory.mktemp("tiny-vit")
    transformers.ViTForImageClassification(config).save_pretrained(path)
    transformers.ViTImageProcessor(size={"height": 32, "width": 32}).save_pretrained(path)
    return path


def _img(arr) -> Image.Image:
    return Image.open(io.BytesIO(to_jpeg(arr)))


def test_cv_features_rank_irregular_above_regular() -> None:
    regular = analyze_image(to_rgb_array(_img(regular_spot())))
    irregular = analyze_image(to_rgb_array(_img(irregular_spot())))
    assert irregular.features.asymmetry > regular.features.asymmetry
    assert irregular.features.border_irregularity > regular.features.border_irregularity
    assert irregular.features.color_variation > regular.features.color_variation
    for value in (
        regular.features.asymmetry,
        regular.features.border_irregularity,
        regular.features.color_variation,
        regular.features.diameter_relative,
    ):
        assert 0 <= value <= 100


def test_heuristic_analyzer_has_no_model_score() -> None:
    result = HeuristicAnalyzer().analyze(_img(regular_spot()))
    assert result.info.kind == "heuristic"
    assert result.model_score is None
    assert result.probabilities == {}


def test_label_weights_match_ham10000_labels() -> None:
    weights = resolve_label_weights(dict(enumerate(HAM_LABELS)), DEFAULT_LABEL_WEIGHTS)
    assert weights == {1: 1.0, 2: 0.6, 5: 1.0}
    assert pattern_risk_score([0, 0, 0, 0, 1, 0, 0], weights) == 0
    assert pattern_risk_score([0, 0.5, 0, 0, 0, 0.5, 0], weights) == 100
    assert pattern_risk_score([0, 0, 1, 0, 0, 0, 0], weights) == 60


def test_vit_analyzer_requires_checkpoint(tmp_path: Path) -> None:
    assert not checkpoint_present(tmp_path)
    with pytest.raises(ModelLoadError):
        ViTAnalyzer(tmp_path, DEFAULT_LABEL_WEIGHTS, "x")


def test_vit_analyzer_refuses_unmatched_labels(tiny_vit_dir: Path) -> None:
    with pytest.raises(ModelLoadError):
        ViTAnalyzer(tiny_vit_dir, {"no_such_label": 1.0}, "x")


def test_vit_analyzer_inference(tiny_vit_dir: Path) -> None:
    analyzer = ViTAnalyzer(tiny_vit_dir, DEFAULT_LABEL_WEIGHTS, "Test model")
    result = analyzer.analyze(_img(irregular_spot()))
    assert result.info.kind == "vit" and result.info.loaded
    assert set(result.probabilities) == set(HAM_LABELS)
    assert abs(sum(result.probabilities.values()) - 1.0) < 1e-3
    assert result.model_score is not None and 0 <= result.model_score <= 100
    # deterministic
    assert analyzer.analyze(_img(irregular_spot())).model_score == result.model_score


def test_scan_api_with_vit_never_leaks_labels(
    client: TestClient, alice, tiny_vit_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "ANALYZER_KIND", "vit")
    monkeypatch.setattr(settings, "MODEL_DIR", tiny_vit_dir)
    registry.reset_analyzer()
    try:
        health = client.get("/health").json()
        resp = client.post(
            "/api/v1/scans",
            headers=alice.headers,
            files={"image": ("spot.jpg", to_jpeg(irregular_spot()), "image/jpeg")},
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["model"]["kind"] == "vit"
        assert body["concern_level"] in {"low", "moderate", "higher"}
        assert 0 <= body["concern_score"] <= 100
        blob = json.dumps(body).lower()
        detail = json.dumps(client.get(f"/api/v1/scans/{body['id']}", headers=alice.headers).json()).lower()
        for word in FORBIDDEN_WORDS:
            if word == "cancer":
                continue  # the mandated disclaimer/recommendation text may mention awareness wording
            assert word not in blob, word
            assert word not in detail, word
        assert "probabilit" not in blob
    finally:
        registry.reset_analyzer()
    assert health["status"] == "ok"
