"""SHAP tree explainer used at inference time.

Persisted at train time (see ``ml/models/train.py``) and loaded lazily by the
API. Generated explanations are stored encrypted alongside the prediction
audit record so clinicians can drill into "why" explanations without
re-running inference.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Sequence

import joblib
import numpy as np

logger = logging.getLogger(__name__)

DEFAULT_PATH = Path("ml/models/xgboost_v1/shap_explainer.pkl")


class ShapExplainer:
    """Wraps the saved TreeExplainer and produces per-prediction SHAP values."""

    def __init__(self, explainer_path: Path = DEFAULT_PATH):
        if not explainer_path.exists():
            raise FileNotFoundError(
                f"SHAP explainer missing at {explainer_path}. Run training first."
            )
        self.explainer = joblib.load(explainer_path)

    def explain(self, features: Sequence[float], feature_names: Sequence[str]):
        arr = np.asarray(features, dtype=np.float32).reshape(1, -1)
        shap_values = self.explainer.shap_values(arr)
        base_value = self.explainer.expected_value
        if isinstance(base_value, (list, np.ndarray)):
            base_value = float(base_value[1])
        else:
            base_value = float(base_value)
        return {
            "base_value": base_value,
            "values": [float(v) for v in shap_values[0]],
            "feature_names": list(feature_names),
            "feature_values": [float(v) for v in arr[0]],
        }

    def top_features(self, explanation: dict, top_k: int = 5) -> list[dict]:
        pairs = sorted(
            zip(explanation["feature_names"], explanation["feature_values"], explanation["values"]),
            key=lambda p: abs(p[2]),
            reverse=True,
        )
        return [
            {"feature": n, "value": float(v), "contribution": float(c)}
            for n, v, c in pairs[:top_k]
        ]
