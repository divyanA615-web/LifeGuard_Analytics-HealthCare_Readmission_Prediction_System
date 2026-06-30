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
    options = rt.SessionOptions()
    options.inter_op_num_threads = int(os.environ.get("INFERENCE_THREADS", "2"))
    options.intra_op_num_threads = int(os.environ.get("INFERENCE_THREADS", "2"))
    options.graph_optimization_level = rt.GraphOptimizationLevel.ORT_ENABLE_ALL
    return rt.InferenceSession(Path(model_path).as_posix(), options)


class InferenceEngine:
    """Stateless wrapper around ONNX Runtime with input validation."""

    def __init__(self, model_path: Path = DEFAULT_MODEL_DIR / "model.onnx"):
        self.session = load_session(model_path)
        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name
        self.expected_features = self.session.get_inputs()[0].shape[1] or None
        logger.info("ONNX model loaded: %s", model_path)

    def validate(self, features: Sequence[float]) -> None:
        arr = np.asarray(features, dtype=np.float32)
        if arr.ndim != 1:
            raise ValueError("features must be 1D")
        if self.expected_features and arr.shape[0] != self.expected_features:
            raise ValueError(
                f"feature length {arr.shape[0]} != expected {self.expected_features}"
            )

    def predict(self, features: Sequence[float]) -> np.ndarray:
        """Return the probability array (n=2) for a single sample."""
        self.validate(features)
        arr = np.asarray(features, dtype=np.float32).reshape(1, -1)
        outs = self.session.run([self.output_name], {self.input_name: arr})
        return outs[0][0]

    def predict_proba_positive(self, features: Sequence[float]) -> float:
        result = self.predict(features)
        return float(result[1] if len(result) == 2 else result[-1])

    def predict_batch(self, matrix: np.ndarray) -> np.ndarray:
        """Return positive-class probabilities for a 2D batch."""
        matrix = np.ascontiguousarray(matrix, dtype=np.float32)
        outs = self.session.run([self.output_name], {self.input_name: matrix})
        return np.asarray(outs[0])[:, 1]
