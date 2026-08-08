"""Backend inference integration test — real ONNX model, real probability wrapper."""
import sys
import pytest
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from ml.models.inference import InferenceEngine  # noqa


@pytest.fixture(scope="module")
def engine():
    artifact = PROJECT_ROOT / "ml" / "models" / "xgboost_v1" / "model.onnx"
    if not artifact.exists():
        pytest.skip(f"ONNX model not found at {artifact}; run training first")
    return InferenceEngine(str(artifact))


def test_xgboost_model_outputs_valid_probabilities(engine):
    """Engine must return two-class logits — never a scalar label index."""
    vec = np.array([55, 6, 45, 12, 0, 0, 1, 2, 3, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0], dtype=np.float32)
    result = engine.predict(vec)
    prob_pos = engine.predict_proba_positive(vec)

    assert result.shape[0] == 2            # [P(neg), P(pos)]
    assert result.dtype in (np.float32, np.float64)
    assert 0.0 <= result[0] <= 1.0
    assert 0.0 <= result[1] <= 1.0
    assert 0.0 <= prob_pos <= 1.0
    assert abs(result[0] + result[1] - 1.0) < 1e-6, f"sum={result[0] + result[1]}"
    assert prob_pos == result[1], "positive-class index mismatch"
