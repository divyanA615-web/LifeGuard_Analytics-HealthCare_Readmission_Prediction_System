"""GLUE between the FastAPI route handlers and the ML pipeline."""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import numpy as np

logger = logging.getLogger(__name__)

MODEL_DIR = Path(os.environ.get("MODEL_ARTIFACT_PATH", "ml/models/xgboost_v1"))
FEATURE_COLUMNS_PATH = MODEL_DIR.parent.parent / "data" / "features" / "feature_columns.json"


@dataclass(slots=True)
class PredictionResult:
    risk_proba: float
    risk_label: str
    explanation: list[dict]
    latency_ms: float
    model_version: str


class MLPipeline:
    """Lazily loaded pipeline used by the FastAPI route layer."""

    def __init__(self):
        self._engine = None
        self._shap = None
        self._shap_failed = False
        self._feature_columns: list[str] | None = None
        self._scaler = None

    @property
    def engine(self):
        if self._engine is None:
            from ml.models.inference import InferenceEngine
            self._engine = InferenceEngine(MODEL_DIR / "model.onnx")
        return self._engine

    @property
    def shap(self):
        if self._shap is None and not self._shap_failed:
            try:
                from ml.models.shap_explainer import ShapExplainer
                self._shap = ShapExplainer(MODEL_DIR / "shap_explainer.pkl")
            except Exception as exc:  # shap/xgboost unpickle can fail
                logger.error("SHAP explainer unavailable: %s", exc)
                self._shap_failed = True
        return self._shap

    @property
    def feature_columns(self) -> list[str]:
        if self._feature_columns is None:
            if FEATURE_COLUMNS_PATH.exists():
                import json

                self._feature_columns = json.loads(FEATURE_COLUMNS_PATH.read_text())
            else:
                self._feature_columns = []
        return self._feature_columns

    @property
    def scaler(self):
        if self._scaler is None:
            scaler_path = MODEL_DIR.parent.parent / "data" / "features" / "scaler.pkl"
            if scaler_path.exists():
                import joblib

                self._scaler = joblib.load(scaler_path)
            else:
                logger.warning("No scaler found at %s – running without scaling", scaler_path)
                self._scaler = None
        return self._scaler

    def predict(self, features: Sequence[float]) -> PredictionResult:
        if not self.feature_columns:
            raise RuntimeError(
                "Feature columns not loaded – make sure training has been run."
            )
        # Accept any length ≤ model features (pad with 0s if ends fall short)
        if len(features) > len(self.feature_columns):
            raise ValueError(
                f"Too many features: got {len(features)}, model expects {len(self.feature_columns)}"
            )
        padded = list(features)
        while len(padded) < len(self.feature_columns):
            padded.append(0.0)

        arr = np.asarray(padded, dtype=np.float32).reshape(1, -1)
        # Note: ONNX export captures raw XGBoost serialization — do NOT scale here,
        # scaling would distort training-inference consistency.

        start = time.perf_counter()
        risk_proba = self.engine.predict_proba_positive(arr.ravel())
        latency_ms = (time.perf_counter() - start) * 1000

        top = []
        if self.shap is not None:
            explanation = self.shap.explain(arr.ravel(), self.feature_columns)
            top = self.shap.top_features(explanation, top_k=5)

        if risk_proba < 0.33:
            risk_label = "LOW"
        elif risk_proba < 0.66:
            risk_label = "MEDIUM"
        else:
            risk_label = "HIGH"

        return PredictionResult(
            risk_proba=float(risk_proba),
            risk_label=risk_label,
            explanation=top,
            latency_ms=latency_ms,
            model_version="xgboost_v1",
        )
