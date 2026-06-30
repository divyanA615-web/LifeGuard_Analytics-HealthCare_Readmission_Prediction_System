"""Model evaluation – AUC, calibration, fairness across demographic slices."""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

import numpy as np
import onnxruntime as rt
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    roc_auc_score,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


def _load_onnx_session(model_path: Path) -> rt.InferenceSession:
    sess = rt.InferenceSession(model_path.as_posix())
    return sess


def _predict_onnx(sess: rt.InferenceSession, X: np.ndarray) -> np.ndarray:
    input_name = sess.get_inputs()[0].name
    results = sess.run(None, {input_name: X.astype(np.float32)})
    # The XGBoost ONNX exports produce multiple [label, proba] outputs.
    # The last one is always the probability tensor.
    for out in reversed(results):
        arr = np.asarray(out)
        if arr.ndim == 2 and arr.shape[1] == 2:
            return arr[:, 1]
        if arr.ndim == 2 and arr.shape[1] == 1:
            return arr[:, 0]
        if arr.ndim == 1:
            return arr
    raise RuntimeError("Could not interpret ONNX outputs")


def _pos_class_rates(y_true: np.ndarray, y_proba: np.ndarray) -> tuple[float, float]:
    if len(np.unique(y_true)) == 1:
        return 0.0, 0.0
    auc_roc = float(roc_auc_score(y_true, y_proba))
    auc_pr = float(average_precision_score(y_true, y_proba))
    return auc_roc, auc_pr


def evaluate(
    features_dir: Path,
    splits_dir: Path,
    model_path: Path = Path("ml/models/xgboost_v1/model.onnx"),
) -> dict:
    feature_columns = json.loads((features_dir / "feature_columns.json").read_text())
    test_path = splits_dir / "test.parquet"
    test = pd.read_parquet(test_path)
    if "readmitted_30d" not in test.columns and "target" in test.columns:
        test["readmitted_30d"] = test["target"]
    y_true = test["readmitted_30d"].values
    X = test[feature_columns].astype(np.float32).values

    sess = _load_onnx_session(model_path)
    probabilities = _predict_onnx(sess, X)
    auc_roc, auc_pr = _pos_class_rates(y_true, probabilities)

    brier = float(brier_score_loss(y_true, probabilities))

    fairness = {}
    if "gender_male" in test.columns:
        for value, label in [(0, "female"), (1, "male")]:
            mask = test["gender_male"].values == value
            if mask.sum() > 50:
                a, p = _pos_class_rates(y_true[mask], probabilities[mask])
                fairness[label] = {"auc_roc": a, "auc_pr": p, "n": int(mask.sum())}

    results = {
        "auc_roc": auc_roc,
        "auc_pr": auc_pr,
        "brier": brier,
        "fairness": fairness,
        "n_test": int(len(y_true)),
        "positive_rate": float(y_true.mean()),
        "predicted_positive_rate": float((probabilities >= 0.5).mean()),
    }
    metrics_path = Path("ml/metrics/evaluation.json")
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.write_text(json.dumps(results, indent=2))
    logger.info("Saved evaluation to %s", metrics_path)
    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--features", type=Path, default=Path("ml/data/features"))
    parser.add_argument("--splits", type=Path, default=Path("ml/data/splits"))
    parser.add_argument("--model", type=Path, default=Path("ml/models/xgboost_v1/model.onnx"))
    args = parser.parse_args()
    evaluate(args.features, args.splits, args.model)
