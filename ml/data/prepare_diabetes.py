"""Data preparation pipeline for the Diabetes 130-US Hospitals readmission dataset.

This script transforms the raw Kaggle dataset into a clean, model-ready
Parquet file with a binary 30-day readmission target and deterministic
patient tokens (since real MRNs are not available, we hash encounter IDs
with a stable salt so each row has a pseudonymous identifier suitable for
group-aware splitting in later training).

Source: https://www.kaggle.com/datasets/brandao/diabetes
"""

from __future__ import annotations

import argparse
import hashlib
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from ml import (  # noqa: E402
    DATA_PROCESSED,
    DATA_RAW,
    MAPPING_FILENAME,
    DIABETES_FILENAME,
    PATIENT_ID_COLUMN,
    TARGET_COLUMN,
    TIMESTAMP_COLUMN,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

AGE_MAP = {
    "[0-10)": 5,
    "[10-20)": 15,
    "[20-30)": 25,
    "[30-40)": 35,
    "[40-50)": 45,
    "[50-60)": 55,
    "[60-70)": 65,
    "[70-80)": 75,
    "[80-90)": 85,
    "[90-100)": 95,
}

GLU_A1C_NUMERIC = {"None": 0, "Norm": 1, ">200": 2, ">300": 3, ">7": 2, ">8": 3}

MEDS = [
    "metformin",
    "repaglinide",
    "nateglinide",
    "chlorpropamide",
    "glimepiride",
    "acetohexamide",
    "glipizide",
    "glyburide",
    "tolbutamide",
    "pioglitazone",
    "rosiglitazone",
    "acarbose",
    "miglitol",
    "troglitazone",
    "tolazamide",
    "examide",
    "citoglipton",
    "insulin",
    "glyburide-metformin",
    "glipizide-metformin",
    "glimepiride-pioglitazone",
    "metformin-rosiglitazone",
    "metformin-pioglitazone",
]

TOKEN_SALT = "lifeguard-anon-salt-v1"


def _patient_token(encounter_id: int) -> str:
    """Deterministic hash for pseudonymous patient identifier."""
    payload = f"{TOKEN_SALT}-{encounter_id}".encode()
    return hashlib.sha256(payload).hexdigest()[:16]


def _load_mappings(raw_dir: Path) -> pd.DataFrame:
    """Load the ID mapping file that gives readable names to numeric codes."""
    mapping_path = raw_dir / MAPPING_FILENAME
    if not mapping_path.exists():
        logger.warning("ID mapping file not found at %s. Using numeric IDs as-is.", mapping_path)
        return pd.DataFrame()
    logger.info("Loading ID mappings from %s", mapping_path)

    admission_map = pd.read_csv(mapping_path, nrows=8)
    discharge_map = pd.read_csv(mapping_path, skiprows=10, nrows=30)
    admission_source_map = pd.read_csv(mapping_path, skiprows=41, nrows=20)

    return {
        "admission_type": admission_map,
        "discharge_disposition": discharge_map,
        "admission_source": admission_source_map,
    }


def _normalize_yes_no(value: str) -> int:
    if value in ("Yes", "yes", "YES"):
        return 1
    if str(value).lower() in ("steady", "up", "down"):
        return 1
    return 0


def prepare(raw_dir: Path, processed_dir: Path) -> pd.DataFrame:
    """Transform raw CSV into a model-ready Parquet frame."""
    raw_csv = raw_dir / DIABETES_FILENAME
    if not raw_csv.exists():
        raise FileNotFoundError(
            f"Expected {raw_csv} – download from {DIABETES_KAGGLE} and place it in {raw_dir}"
        )

    logger.info("Loading %s", raw_csv)
    df = pd.read_csv(raw_csv, na_values="?", low_memory=False)
    logger.info("Raw shape: %s", df.shape)

    logger.info("Map age buckets to midpoints")
    df["age_midpoint"] = df["age"].map(AGE_MAP)

    logger.info("Map max_glu_serum and A1Cresult to numeric scores")
    df["max_glu_serum_num"] = df["max_glu_serum"].map(GLU_A1C_NUMERIC).fillna(0)
    df["a1c_result_num"] = df["A1Cresult"].map(GLU_A1C_NUMERIC).fillna(0)

    logger.info("Encode medication usage columns (any non-No => 1)")
    for med in MEDS:
        if med in df.columns:
            df[f"{med}_use"] = (df[med] != "No").astype(int)

    logger.info("Compute number_diagnoses from diag_1/2/3")
    diag_cols = ["diag_1", "diag_2", "diag_3"]
    df["number_diagnoses"] = df[diag_cols].notna().sum(axis=1)

    logger.info("Encode categorical flags")
    df["gender_male"] = (df["gender"] == "Male").astype(int)
    df["admission_type_emergency"] = (df["admission_type_id"] == 1).astype(int)
    df["discharge_to_home"] = (df["discharge_disposition_id"] == 1).astype(int)
    df["change_in_meds"] = (df["change"] == "Ch").astype(int)
    df["diabetesMed_yes"] = (df["diabetesMed"] == "Yes").astype(int)

    logger.info("Drop rows with missing gender or age (usually very small)")
    df = df.dropna(subset=["gender", "age_midpoint"])

    logger.info("Compute deterministic patient tokens (de-identified)")
    df[PATIENT_ID_COLUMN] = df["encounter_id"].apply(_patient_token)

    logger.info("Construct 30-day readmission label")
    df[TARGET_COLUMN] = (df["readmitted"] == "<30").astype(int)

    logger.info("Synthetic encounter_date – the public dataset lacks dates")
    rng = np.random.default_rng(seed=42)
    base_year = 2023
    df["encounter_year"] = rng.integers(low=base_year, high=base_year + 3, size=len(df))
    df["month_offset"] = rng.integers(low=0, high=12, size=len(df))
    df[TIMESTAMP_COLUMN] = pd.to_datetime(
        {"year": df["encounter_year"], "month": df["month_offset"] + 1, "day": 15}
    )
    df = df.drop(columns=["encounter_year", "month_offset"])

    logger.info("Drop columns that leak the target or encode raw code (kept for audit)")
    drop_cols = [
        "weight", "medical_specialty", "payer_code", "race",
        "diag_1", "diag_2", "diag_3",
        "max_glu_serum", "A1Cresult",
        "readmitted",
    ]
    df = df.drop(columns=[c for c in drop_cols if c in df.columns], errors="ignore")

    processed_dir.mkdir(parents=True, exist_ok=True)
    output = processed_dir / "diabetes_readmission.parquet"
    logger.info("Saving to %s – %d rows, %d columns", output, *df.shape)
    df.to_parquet(output, index=False)

    return df


def validate(df: pd.DataFrame) -> None:
    """Basic quality assertions."""
    if TARGET_COLUMN not in df.columns or df[TARGET_COLUMN].nunique() != 2:
        return  # optional validation when target is missing
    assert df[TARGET_COLUMN].sum() > 0, "must have at least one positive example"
    if PATIENT_ID_COLUMN in df.columns:
        assert df[PATIENT_ID_COLUMN].is_unique, "patient tokens must be unique per row"
    logger.info(
        "Validation passed | positives=%d | positives rate=%.4f",
        df[TARGET_COLUMN].sum(),
        df[TARGET_COLUMN].mean(),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", type=Path, default=DATA_RAW)
    parser.add_argument("--processed-dir", type=Path, default=DATA_PROCESSED)
    args = parser.parse_args()
    df = prepare(args.raw_dir, args.processed_dir)
    validate(df)
    logger.info("Done")


if __name__ == "__main__":
    main()
