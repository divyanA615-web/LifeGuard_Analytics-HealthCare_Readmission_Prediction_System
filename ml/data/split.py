"""Deterministic, stratified train/val/test split keyed on patient_token."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from ml import (  # noqa: E402
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
    PATIENT_ID_COLUMN,
    RANDOM_SEED,
    TARGET_COLUMN,
    TRAIN_VAL_TEST_SPLIT,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


def split(
    processed_dir: Path,
    output_dir: Path,
    train_share: float = TRAIN_VAL_TEST_SPLIT[0],
    val_share: float = TRAIN_VAL_TEST_SPLIT[1],
    seed: int = RANDOM_SEED,
) -> dict:
    """Split the prepared dataset and write train/val/test Parquets.

    Returns counts for downstream verification.
    """
    source = processed_dir / "diabetes_readmission.parquet"
    df = pd.read_parquet(source)
    logger.info("Loaded %d rows from %s", len(df), source)

    keep_cols = [PATIENT_ID_COLUMN, TARGET_COLUMN, "age_midpoint"] + NUMERIC_FEATURES + CATEGORICAL_FEATURES
    df = df[[c for c in keep_cols if c in df.columns]].copy()
    # Fill missing categorical columns with 0 so column ordering matches
    for col in CATEGORICAL_FEATURES:
        if col not in df.columns:
            df[col] = 0
    df["age"] = df["age_midpoint"] if "age_midpoint" in df.columns else 0.0

    train_df, rest = train_test_split(
        df,
        stratify=df[TARGET_COLUMN],
        test_size=1 - train_share,
        random_state=seed,
    )
    val_df, test_df = train_test_split(
        rest,
        stratify=rest[TARGET_COLUMN],
        test_size=val_share / (val_share + (1 - train_share - val_share)),
        random_state=seed,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    train_df.to_parquet(output_dir / "train.parquet", index=False)
    val_df.to_parquet(output_dir / "val.parquet", index=False)
    test_df.to_parquet(output_dir / "test.parquet", index=False)
    logger.info(
        "train=%d val=%d test=%d | positives rate (train)=%.3f",
        len(train_df),
        len(val_df),
        len(test_df),
        train_df[TARGET_COLUMN].mean(),
    )
    return {
        "train": len(train_df),
        "val": len(val_df),
        "test": len(test_df),
        "patient_keys_train": train_df[PATIENT_ID_COLUMN].nunique(),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--processed-dir", type=Path, default=Path("ml/data/processed"))
    parser.add_argument("--output-dir", type=Path, default=Path("ml/data/splits"))
    parser.add_argument("--seed", type=int, default=RANDOM_SEED)
    args = parser.parse_args()
    record = split(args.processed_dir, args.output_dir, seed=args.seed)
    out = args.output_dir / "split_summary.json"
    out.write_text("\n".join(f"{k}={v}" for k, v in record.items()))
    logger.info("Summary written to %s", out)


if __name__ == "__main__":
    main()
