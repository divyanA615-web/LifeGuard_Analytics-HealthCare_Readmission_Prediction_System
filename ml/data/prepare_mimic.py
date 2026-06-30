"""MIMIC-IV data preparation (requires PhysioNet credential).

Produces the same Parquet schema as the Diabetes dataset so downstream
models can train on either source. Computes a 30-day readmission label
from the MIMIC-IV `admissions` table.

MIMIC-IV: https://physionet.org/content/mimiciv/2.2/
"""


from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))

from ml import (  # noqa: E402
    DATA_PROCESSED,
    DATA_RAW,
    PATIENT_ID_COLUMN,
    TARGET_COLUMN,
    TIMESTAMP_COLUMN,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


def derive_readmission_label(admissions: pd.DataFrame) -> pd.DataFrame:
    """.Compute 30-day readmission per (subject_id, hadm_id) using lead timestamps."""
    admissions = admissions.sort_values(["subject_id", "admittime"]).reset_index(drop=True)
    admissions["next_admittime"] = admissions.groupby("subject_id")["admittime"].shift(-1)
    admissions["days_to_next"] = (
        admissions["next_admittime"] - admissions["dischtime"]
    ).dt.days
    admissions[TARGET_COLUMN] = (
        (admissions["days_to_next"] >= 0) & (admissions["days_to_next"] <= 30)
    ).astype(int)
    return admissions


def prepare(mimic_dir: Path, processed_dir: Path) -> pd.DataFrame:
    """Aggregate MIMIC-IV tables into a single training table."""
    admissions = pd.read_csv(
        mimic_dir / "admissions.csv.gz",
        parse_dates=["admittime", "dischtime"],
        compression="gzip",
    )
    patients = pd.read_csv(mimic_dir / "patients.csv.gz", compression="gzip")
    diagnoses = pd.read_csv(mimic_dir / "diagnoses_icd.csv.gz", compression="gzip")

    admissions = derive_readmission_label(admissions)

    encounters = (
        patients[["subject_id", "gender", "anchor_age"]]
        .merge(admissions, on="subject_id", how="inner")
        .rename(columns={"anchor_age": "age", "gender_male": "label"})
    )
    encounters["gender_male"] = (encounters["gender"] == "M").astype(int)

    diag_counts = (
        diagnoses.groupby("hadm_id")["icd_code"].nunique().reset_index(name="number_diagnoses")
    )
    encounters = encounters.merge(diag_counts, on="hadm_id", how="left").fillna(
        {"number_diagnoses": 0}
    )
    encounters["time_in_hospital"] = (
        encounters["dischtime"] - encounters["admittime"]
    ).dt.days
    encounters["number_inpatient"] = admissions.groupby("subject_id")["hadm_id"].cumcount()

    encounters[PATIENT_ID_COLUMN] = encounters["subject_id"].astype(str)
    encounters[TIMESTAMP_COLUMN] = encounters["admittime"].dt.strftime("%Y-%m-%d")

    cols = [
        PATIENT_ID_COLUMN,
        TIMESTAMP_COLUMN,
        TARGET_COLUMN,
        "age",
        "gender_male",
        "admission_type",
        "insurance",
        "time_in_hospital",
        "number_diagnoses",
        "number_inpatient",
    ]
    encounters = encounters.loc[:, [c for c in cols if c in encounters.columns]]

    processed_dir.mkdir(parents=True, exist_ok=True)
    output = processed_dir / "mimic_readmission.parquet"
    encounters.to_parquet(output, index=False)
    logger.info("Saved %s (%d rows)", output, len(encounters))
    return encounters


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mimic-dir", type=Path, default=DATA_RAW / "mimic-iv")
    parser.add_argument("--processed-dir", type=Path, default=DATA_PROCESSED)
    args = parser.parse_args()
    if not args.mimic_dir.exists():
        raise FileNotFoundError(
            f"{args.mimic_dir} not found. Apply for MIMIC-IV credentialing first."
        )
    prepare(args.mimic_dir, args.processed_dir)


if __name__ == "__main__":
    main()
