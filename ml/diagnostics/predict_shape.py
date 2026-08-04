"""Quick model diagnosis.

Looks up scaler shape vs model scaler usage and predict response on fixed input.

Run inside the running container:
    docker exec -e PYTHONPATH=/app lifeguard-backend python ml/diagnostics/predict_shape.py
"""
import json
import sys
from pathlib import Path

import joblib
import numpy as np

# Ensure /app/ml is importable
ROOT = Path("/app")
sys.path.insert(0, str(ROOT))

SCALER = ROOT / "ml/data/features/scaler.pkl"
MODEL = ROOT / "ml/models/xgboost_v1/model.onnx"
FEATURES = ROOT / "ml/data/features/feature_columns.json"

scaler = joblib.load(SCALER)
from ml.models.inference import InferenceEngine
from ml.models.shap_explainer import ShapExplainer

engine = InferenceEngine(MODEL)
shap = ShapExplainer(ROOT / "ml/models/xgboost_v1/shap_explainer.pkl")

cols = json.loads(FEATURES.read_text())
input_vec = np.array([
    70, 5, 30, 2, 10,
    0, 0, 0, 3,
    0, 0,
    1, 1, 1,
    0,
    1, 0, 1, 1
], dtype=np.float32)

print("Feature columns count:", len(cols))
print("Scaler imputer expected:", scaler.named_steps["imputer"].n_features_in_)
print("Scaler scaler expected:", scaler.named_steps["scaler"].n_features_in_)
print("Model expected features:", engine.session.get_inputs()[0].shape[1])

try:
    scaled = scaler.transform(input_vec.reshape(1, -1))
    print("scaled shape:", scaled.shape)
    print("p @ engine with scaled:", engine.predict_proba_positive(scaled.ravel()))
except Exception as e:
    print("scale fail:", e)

print("raw p @ engine with raw vec: ", engine.predict_proba_positive(input_vec))

# Probe edges
for v in [0.0, 0.5, 1.0, 5.0]:
    vec = np.full((1, 19), v)
    prob = engine.predict_proba_positive(vec.ravel())
    print(f"all-{v} -> p={prob}")