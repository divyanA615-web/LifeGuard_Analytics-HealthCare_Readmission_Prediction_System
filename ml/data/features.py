"""Feature engineering pipeline.

Loads the prepared Parquet, creates the numeric/boolean feature matrix,
serialises a scaler (used by both training and inference) and writes a
feature_columns.json that captures the exact ordering expected by the
model at inference time.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import joblib
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

sys.path.append(str(Path(__file__).resolve().parents[1]))

from ml import CATEGORICAL_FEATURES, NUMERIC_FEATURES, PATIENT_ID_COLUMN  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

NUMERIC_DEFAULTS = {
    "age": 50.0,
    "time_in_hospital": 4.0,
    "num_lab_procedures": 40.0,
    "num_procedures": 1.0,
    "num_medications": 14.0,
    "number_outpatient": 0.0,
    "number_emergency": 0.0,
    "number_inpatient": 0.0,
    "number_diagnoses": 3.0,
    "max_glu_serum_num": 0.0,
    "a1c_result_num": 0.0,
}


def _enforce_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Ensure every required numeric column exists and is float-typed."""
    missing = [c for c in columns if c not in df.columns]
    if missing:
        logger.warning("Missing columns filled with zero: %s", missing)
        for c in missing:
            df[c] = NUMERIC_DEFAULTS.get(c, 0.0)
    return df[columns].astype(float)


def build_features(
    splits_dir: Path,
    output_dir: Path,
):
    train = pd.read_parquet(splits_dir / "train.parquet")
    val = pd.read_parquet(splits_dir / "val.parquet")
    test = pd.read_parquet(splits_dir / "test.parquet")
    logger.info("Loaded splits train/val/test=%d/%d/%d", len(train), len(val), len(test))

    all_cols = NUMERIC_FEATURES + CATEGORICAL_FEATURES
    x_train = _enforce_columns(train, NUMERIC_FEATURES)
    x_train = pd.concat([x_train, train[[c for c in CATEGORICAL_FEATURES if c in train.columns]]], axis=1)

    scaler = Pipeline(
        steps=[
            ("imputer", __import__("sklearn.impute", fromlist=["SimpleImputer"]).SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    scaler.fit(x_train[NUMERIC_FEATURES])

    output_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(scaler, output_dir / "scaler.pkl")

    feature_columns = NUMERIC_FEATURES + CATEGORICAL_FEATURES
    (output_dir / "feature_columns.json").write_text(
        json.dumps(feature_columns, indent=2)
    )
    logger.info("Feature columns: %s", feature_columns)

    artefact_paths = {
        "train_features": output_dir / "train_X.parquet",
        "val_features": output_dir / "val_X.parquet",
        "test_features": output_dir / "test_X.parquet",
    }
    for split_name, frame in [("train", train), ("val", val), ("test", test)]:
        x = _enforce_columns(frame, NUMERIC_FEATURES)
        cats = frame[[c for c in CATEGORICAL_FEATURES if c in frame.columns]]
        full = pd.concat([x, cats], axis=1)
        full.to_parquet(artefact_paths[f"{split_name}_features"], index=False)
    logger.info("Wrote feature matrices to %s", output_dir)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--splits", type=Path, default=Path("ml/data/splits"))
    parser.add_argument("--output", type=Path, default=Path("ml/data/features"))
    args = parser.parse_args()
    build_features(args.splits, args.output)


if __name__ == "__main__":
    main()
