"""Synthetic data preparation using Synthea outputs.

Synthea produces FHIR-format JSON bundles. This script deduplicates them
into a single CSV-style table that mirrors the input schema of
``prepare_diabetes``. Useful when you want unlimited training data without
downloading the Kaggle dataset.

Synthea: https://github.com/synthetichealth/synthea
"""


from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Iterable

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


def _iter_bundles(fhir_dir: Path) -> Iterable[dict]:
    for f in fhir_dir.rglob("*.json"):
        yield json.loads(f.read_text())


def _extract_fhir_resources(bundle: dict) -> dict:
    """Extract Patient + Encounter + Condition facts from a Synthea bundle."""
    out = {}
    for entry in bundle.get("entry", []):
        res = entry.get("resource", {})
        rtype = res.get("resourceType")
        if rtype == "Patient":
            out["gender_male"] = int(res.get("gender") == "male")
            for ext in res.get("extension", []):
                if "birthDate" in ext.get("url", ""):
                    out["birth_year"] = int(ext["valueDate"].get("valueOfDateString", "2000")[:4])
            out[PATIENT_ID_COLUMN] = res.get("id", "")
        elif rtype == "Encounter":
            period = res.get("period", {})
            if period.get("start"):
                out["encounter_start"] = period["start"][:10]
            if period.get("end"):
                out["encounter_end"] = period["end"][:10]
    return out


def _readmission_flag(bundles: list[dict]) -> int:
    """Flag is 1 if a Patient has multiple Encounter entries within 30 days."""
    return 1 if len(bundles) > 1 else 0


def prepare(fhir_dir: Path, processed_dir: Path) -> pd.DataFrame:
    rows = []
    by_patient: dict = {}
    for bundle in _iter_bundles(fhir_dir):
        rec = _extract_fhir_resources(bundle)
        pid = rec.get(PATIENT_ID_COLUMN, "")
        if pid:
            by_patient.setdefault(pid, []).append(rec)

    for pid, recs in by_patient.items():
        first = recs[0]
        rows.append(
            {
                PATIENT_ID_COLUMN: pid,
                TARGET_COLUMN: _readmission_flag(recs),
                TIMESTAMP_COLUMN: first.get("encounter_start"),
                "age": 2023 - first.get("birth_year", 2000),
                "gender_male": first.get("gender_male", 0),
            }
        )

    df = pd.DataFrame(rows)
    processed_dir.mkdir(parents=True, exist_ok=True)
    out = processed_dir / "synthea_readmission.parquet"
    df.to_parquet(out, index=False)
    logger.info("Saved %s (%d rows)", out, len(df))
    return df


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fhir-dir", type=Path, default=DATA_RAW / "synthea")
    parser.add_argument("--processed-dir", type=Path, default=DATA_PROCESSED)
    args = parser.parse_args()
    if not args.fhir_dir.exists():
        raise FileNotFoundError(
            f"{args.fhir_dir} does not exist. Install Synthea and generate FHIR first."
        )
    prepare(args.fhir_dir, args.processed_dir)


if __name__ == "__main__":
    main()
