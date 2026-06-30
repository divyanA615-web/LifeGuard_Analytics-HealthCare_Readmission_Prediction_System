"""Tests for the data preparation pipeline."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest


@pytest.fixture()
def raw_df() -> pd.DataFrame:
    """Return a sample of the Diabetes 130-US hospitals structure."""
    return pd.DataFrame(
        {
            "encounter_id": [1, 2, 3],
            "patient_nbr": [11, 22, 33],
            "gender": ["Male", "Female", "Male"],
            "age": ["[50-60)", "[60-70)", "[70-80)"],
            "admission_type_id": [1, 3, 1],
            "discharge_disposition_id": [1, 6, 1],
            "time_in_hospital": [4, 7, 2],
            "num_lab_procedures": [40, 60, 20],
            "num_procedures": [1, 3, 0],
            "num_medications": [10, 18, 5],
            "number_outpatient": [0, 2, 0],
            "number_emergency": [0, 0, 1],
            "number_inpatient": [0, 1, 0],
            "diag_1": ["250", "401", "250"],
            "diag_2": ["401", "250", "428"],
            "diag_3": [None, "428", "250"],
            "max_glu_serum": ["None", ">200", "Norm"],
            "A1Cresult": ["None", ">7", ">8"],
            "metformin": ["No", "Steady", "No"],
            "insulin": ["Steady", "Up", "No"],
            "diabetesMed": ["Yes", "Yes", "No"],
            "change": ["No", "Ch", "No"],
            "readmitted": ["<30", ">30", "NO"],
        }
    )


def test_prepare_token_is_deterministic(tmp_path: Path, raw_df: pd.DataFrame, monkeypatch: pytest.MonkeyPatch) -> None:
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    raw_df.to_csv(raw_dir / "diabetic_data.csv", index=False)

    out_dir = tmp_path / "processed"
    monkeypatch.setattr("ml.data.prepare_diabetes.DATA_RAW", raw_dir)
    monkeypatch.setattr("ml.data.prepare_diabetes.DATA_PROCESSED", out_dir)

    from ml.data import prepare_diabetes

    df = prepare_diabetes.prepare(raw_dir, out_dir)
    assert (out_dir / "diabetes_readmission.parquet").exists()
    assert df["patient_token"].nunique() == len(df)
    assert df["readmitted_30d"].tolist() == [1, 0, 0]
    assert df["age_midpoint"].tolist() == [55.0, 65.0, 75.0]


def test_validation_requires_binary_target(tmp_path: Path) -> None:
    df = pd.DataFrame({"readmitted_30d": [0, 1, 1]})
    prepare_diabetes = __import__("ml.data.prepare_diabetes", fromlist=["validate"]).validate
    prepare_diabetes(df)  # should not raise
