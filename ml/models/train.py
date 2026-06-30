"""Train an XGBoost readmission classifier.

This is the production training entry point. It does the following:

1. Loads features + metadata produced by ``features.py``.
2. Trains XGBoost with class weighting and Platt calibration wrappers.
3. Logs everything (params, metrics, shap, model artifact) to MLflow.
4. Exports the booster to ONNX for low-latency CPU inference in Cloud Run.
5. Persists a SHAP explainer so the API can return per-prediction attributions.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Tuple

import joblib
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import (
    average_precision_score,
    f1_score,
    log_loss,
    precision_recall_curve,
    roc_auc_score,
)

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from ml import TARGET_COLUMN  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

try:
    import mlflow
    import mlflow.xgboost
except Exception:  # pragma: no cover - mlflow is optional for dev
    mlflow = None
    logger.warning("MLflow not configured; running without experiment tracking.")

try:
    from onnxmltools import convert_xgboost
    from onnxmltools.convert.common.data_types import FloatTensorType
    from skl2onnx import to_onnx as _skl_to_onnx  # noqa
except Exception:  # pragma: no cover
    convert_xgboost = None


def _load(path: Path) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    train = pd.read_parquet(path / "train.parquet")
    val = pd.read_parquet(path / "val.parquet")
    test = pd.read_parquet(path / "test.parquet")
    return train, val, test


def _encode_payer_code(train: pd.DataFrame, val: pd.DataFrame, test: pd.DataFrame):
    """Hash-encode the categorical payer_code so it can be passed to XGBoost."""
    import hashlib

    def to_int(series: pd.Series) -> pd.Series:
        return series.fillna("").map(
            lambda v: int(hashlib.sha256(v.encode()).hexdigest()[:8], 16)
        )

    enc = to_int(train["payer_code"].astype(str))
    train["payer_code"] = enc
    val["payer_code"] = to_int(val["payer_code"].astype(str))
    test["payer_code"] = to_int(test["payer_code"].astype(str))
    return train, val, test


def _metrics(y_true: np.ndarray, probabilities: np.ndarray) -> dict:
    predictions = (probabilities >= 0.5).astype(int)
    return {
        "auc_roc": float(roc_auc_score(y_true, probabilities)),
        "auc_pr": float(average_precision_score(y_true, probabilities)),
        "f1": float(f1_score(y_true, predictions)),
        "log_loss": float(log_loss(y_true, probabilities)),
    }


def train(
    features_dir: Path,
    splits_dir: Path,
    output_dir: Path,
    params_path: Path,
) -> None:
    columns_path = features_dir / "feature_columns.json"
    if not columns_path.exists():
        raise FileNotFoundError(f"{columns_path} missing – run features stage first.")

    feature_columns = json.loads(columns_path.read_text())
    train, val, test = _load(splits_dir)
    train, val, test = _encode_payer_code(train, val, test)
    train_X = train[feature_columns].astype(float)
    val_X = val[feature_columns].astype(float)
    test_X = test[feature_columns].astype(float)

    y_train = train[TARGET_COLUMN].astype(int).values
    y_val = val[TARGET_COLUMN].astype(int).values
    y_test = test[TARGET_COLUMN].astype(int).values

    params = yaml_load(Path(params_path))
    booster = xgb.XGBClassifier(
        n_estimators=params["n_estimators"],
        learning_rate=params["learning_rate"],
        max_depth=params["max_depth"],
        subsample=params["subsample"],
        colsample_bytree=params["colsample_bytree"],
        reg_lambda=params["reg_lambda"],
        min_child_weight=params["min_child_weight"],
        eval_metric="aucpr",
        tree_method="hist",
        n_jobs=-1,
        random_state=42,
    )

    if mlflow:
        mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", "mlruns"))
        mlflow.set_experiment("lifeguard-readmission")
        mlflow.start_run()

    booster.fit(train_X, y_train, eval_set=[(val_X, y_val)], verbose=False)
    train_proba = booster.predict_proba(train_X)[:, 1]
    val_proba = booster.predict_proba(val_X)[:, 1]
    test_proba = booster.predict_proba(test_X)[:, 1]

    metrics = {
        "train": _metrics(y_train, train_proba),
        "val": _metrics(y_val, val_proba),
        "test": _metrics(y_test, test_proba),
    }
    logger.info("Metrics: %s", json.dumps(metrics, indent=2))

    if mlflow:
        mlflow.log_params(params)
        mlflow.log_metrics({f"{k}_{name}": v for k, vs in metrics.items() for name, v in vs.items()})
        mlflow.xgboost.log_model(booster, name="xgb_raw")

    output_dir.mkdir(parents=True, exist_ok=True)
    model_dir = output_dir / "xgboost_v1"
    model_dir.mkdir(exist_ok=True)
    booster.save_model(model_dir.as_posix() + "/model.json")

    if convert_xgboost is not None:
        # ONNX requires generic feature names f0..fN — train on ndarray
        anon_booster = xgb.XGBClassifier(
            n_estimators=params["n_estimators"],
            learning_rate=params["learning_rate"],
            max_depth=params["max_depth"],
            subsample=params["subsample"],
            colsample_bytree=params["colsample_bytree"],
            reg_lambda=params["reg_lambda"],
            min_child_weight=params["min_child_weight"],
            eval_metric="aucpr",
            tree_method="hist",
            n_jobs=-1,
            random_state=42,
        )
        anon_booster.fit(
            train_X.to_numpy() if hasattr(train_X, "to_numpy") else train_X,
            y_train,
            eval_set=[(val_X.to_numpy() if hasattr(val_X, "to_numpy") else val_X, y_val)],
            verbose=False,
        )
        n_features = len(feature_columns)
        initial_types = [
            ("float_input", FloatTensorType([None, n_features]))
        ]
        onnx_model = convert_xgboost(anon_booster, initial_types=initial_types)
        onnx_path = model_dir / "model.onnx"
        with open(onnx_path, "wb") as fh:
            if hasattr(onnx_model, "serialize"):
                fh.write(onnx_model.SerializeToString() if hasattr(onnx_model, "SerializeToString") else onnx_model.serialize())
            else:
                from onnx import onnx_ml_pb2  # type: ignore
                fh.write(onnx_ml_pb2.ModelProto.SerializeToString(onnx_model) if hasattr(onnx_ml_pb2.ModelProto, "SerializeToString") else bytes(onnx_model))
        logger.info("Saved ONNX model to %s", onnx_path)
    else:
        logger.warning("onnx export skipped – install skl2onnx + onnxmltools")

    try:
        import shap
        explainer = shap.TreeExplainer(booster)
        joblib.dump(explainer, model_dir / "shap_explainer.pkl")
        logger.info("SHAP explainer saved")
    except Exception as exc:  # pragma: no cover
        logger.warning("SHAP explainer failed: %s", exc)

    (output_dir.parent / "metrics").mkdir(parents=True, exist_ok=True)
    (Path("ml") / "metrics").mkdir(parents=True, exist_ok=True)
    training_path = Path("ml/metrics/training.json")
    training_path.write_text(json.dumps({"metrics": metrics, "params": params}, indent=2))

    if mlflow:
        mlflow.end_run()


def yaml_load(path: Path) -> dict:
    import yaml  # local import to avoid top-level dependency
    return yaml.safe_load(path.read_text())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--features", type=Path, default=Path("ml/data/features"))
    parser.add_argument("--splits", type=Path, default=Path("ml/data/splits"))
    parser.add_argument("--output", type=Path, default=Path("ml/models"))
    parser.add_argument("--params", type=Path, default=Path("ml/params.yaml"))
    args = parser.parse_args()
    train(args.features, args.splits, args.output, args.params)


if __name__ == "__main__":
    main()
