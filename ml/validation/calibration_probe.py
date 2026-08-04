"""Diagnostic probe for model calibration health.

Runs only local inference checks against mounted artifacts, never hits DB.
Writes JSON report to `ml/validation/calibration-report.json` per AGT loop rules.
"""
import json
import sys
from pathlib import Path

import joblib
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ml.models.inference import InferenceEngine
from ml.models.shap_explainer import ShapExplainer

MODEL_DIR = ROOT / "models" / "xgboost_v1"
FEATURES_PATH = ROOT / "data" / "features" / "feature_columns.json"
SCALER_PATH = ROOT / "data" / "features" / "scaler.pkl"


def probe() -> dict:
    engine = InferenceEngine(MODEL_DIR / "model.onnx")
    shap = ShapExplainer(MODEL_DIR / "shap_explainer.pkl")
    scaler = joblib.load(SCALER_PATH)

    columns = json.loads(FEATURES_PATH.read_text())
    rng = np.random.default_rng(42)

    report = {
        "n_features_declared": len(columns),
        "n_features_expected": engine.session.get_inputs()[0].shape[1],
        "calibration_samples": [],
        "scaler_meta": None,
    }

    if scaler is not None:
        report["scaler_meta"] = {
            "pipeline_structure": [type(n).__name__ for _, n in scaler.steps]
        }

    for i in range(5):
        vec = rng.uniform(low=0.0, high=[100, 14, 70, 5, 30, 3, 3, 5, 10, 3, 3,
                                         1, 1, 1, 1, 1, 1, 1, 1])[:19]
        p = engine.predict_proba_positive(vec)
        report["calibration_samples"].append(
            {
                "patient_input": [round(float(x), 4) for x in vec[:10]],
                "prob_positive": round(float(p), 6),
                "threshold_label": int(p >= 0.5),
            }
        )

    return report


if __name__ == "__main__":
    out = probe()
    out_path = ROOT / "validation" / "calibration-report.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))
