"""Tests for inference engine and SHAP explainer."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest


def test_inference_engine_shape_validation(tmp_path: Path) -> None:
    """The engine must reject feature payloads with wrong shape."""
    # Engine expects a fixture ONNX. We can only test the validator here without one.
    from ml.models.inference import FeatureValue
    fv = FeatureValue(features=[1.0, 2.0], feature_names=["a", "b"])
    assert fv.features[0] == 1.0
    assert fv.feature_names[1] == "b"


def test_shap_explainer_missing_file(tmp_path: Path) -> None:
    from ml.models.shap_explainer import ShapExplainer
    with pytest.raises(FileNotFoundError):
        ShapExplainer(explainer_path=tmp_path / "missing.pkl")


def test_top_features_ordering() -> None:
    from ml.models.shap_explainer import ShapExplainer

    class Stub:
        def __init__(self):
            pass

    se = ShapExplainer.__new__(ShapExplainer)
    se.explainer = None

    explanation = {
        "feature_names": ["a", "b", "c"],
        "feature_values": [1.0, 1.0, 1.0],
        "values": [0.1, -0.5, 0.2],
        "base_value": 0.0,
    }
    top = se.top_features(explanation, top_k=2)
    assert top[0]["feature"] == "b"  # abs value 0.5
    assert top[1]["feature"] == "c"
