"""ONNX inference engine used by the FastAPI backend.

Loads the model once per process and exposes a thread-safe predict().
The same module is reused in batch jobs and stress tests.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import numpy as np
import onnxruntime as rt

logger = logging.getLogger(__name__)

DEFAULT_MODEL_DIR = Path("ml/models/xgboost_v1")


@dataclass
class FeatureValue:
    """Single prediction feature payload."""

    features: Sequence[float]
    feature_names: Sequence[str]


def load_session(model_path: str | os.PathLike = DEFAULT_MODEL_DIR / "model.onnx") -> rt.InferenceSession:
    """Create and configure an ONNX inference session."""
    p = Path(model_path)
    if p.is_dir():
        p = p / "model.onnx"
    options = rt.SessionOptions()
    options.inter_op_num_threads = int(os.environ.get("INFERENCE_THREADS", "2"))
    options.intra_op_num_threads = int(os.environ.get("INFERENCE_THREADS", "2"))
    options.graph_optimization_level = rt.GraphOptimizationLevel.ORT_ENABLE_ALL
    return rt.InferenceSession(p.as_posix(), options)


class InferenceEngine:
    """Stateless wrapper around ONNX Runtime with input validation."""

    def __init__(self, model_path: Path = DEFAULT_MODEL_DIR / "model.onnx"):
        self.session = load_session(model_path)
        self.input_name = self.session.get_inputs()[0].name
        # XGBoost ONNX exposes [label, probabilities] — we want probabilities
        self.probabilities_name = self.session.get_outputs()[1].name
        self.expected_features = self.session.get_inputs()[0].shape[1] or None
        logger.info("ONNX model loaded")

    def predict_batch_logits(self, features: Sequence[float]) -> np.ndarray:
        """Return FULL probability pair for a 1-sample row."""
        self.validate(features)
        arr = np.asarray(features, dtype=np.float32).reshape(1, -1)
        results = self.session.run([self.probabilities_name], {self.input_name: arr})
        return np.asarray(results[0])

    def validate(self, features: Sequence[float]) -> None:
        arr = np.asarray(features, dtype=np.float32)
        if arr.ndim != 1:
            raise ValueError("features must be 1D")
        if self.expected_features and arr.shape[0] != self.expected_features:
            raise ValueError(
                f"feature length {arr.shape[0]} != expected {self.expected_features}"
            )

    def predict(self, features: Sequence[float]) -> np.ndarray:
        """Return [P(negative), P(readmitted)] probabilities from ONNX engine."""
        self.validate(features)
        arr = np.asarray(features, dtype=np.float32).reshape(1, -1)
        results = self.session.run([self.probabilities_name], {self.input_name: arr})
        result = np.asarray(results[0]).reshape(1, -1)  # shape becomes (1,2)
        return result[0]

    def predict_proba_positive(self, features: Sequence[float]) -> float:
        pos_probability = self.predict(features)[-1]
        return float(pos_probability)

    def predict_batch(self, matrix: np.ndarray) -> np.ndarray:
        """Return positive-class probabilities for a 2D batch."""
        matrix = np.ascontiguousarray(matrix, dtype=np.float32)
        results = self.session.run([self.probabilities_name], {self.input_name: matrix})
        result = np.asarray(results[0])
        if result.ndim == 2:
            if result.shape[-1] == 2:
                return result[:, 1]
            if result.shape[-1] == 1:
                return result[:, 0]
        if result.ndim == 1:
            return result
        return result[:, -1]
