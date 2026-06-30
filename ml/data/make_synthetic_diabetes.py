"""SynthDiab v1 - tiny synthetic diabetes-style dataset.

We ship this ONLY so the prepare/split/train pipeline is exercisable on day
one without external credentials. The training metrics it produces are not
representative of the real model.

Do NOT use this CSV for clinical validation. Replace with the Kaggle
Diabetes 130-US Hospitals dataset (https://www.kaggle.com/datasets/brandao/diabetes)
as soon as your credentials are set.
"""

from __future__ import annotations

import csv
import random
from pathlib import Path

random.seed(0xBEEF)

AGE_BANDS = ["[0-10)", "[10-20)", "[20-30)", "[30-40)", "[40-50)", "[50-60)", "[60-70)", "[70-80)", "[80-90)", "[90-100)"]
DIAG_PREFIXES = ["250", "401", "428", "276", "E11", "I10", "J45", "N18", "K21"]

def _age() -> str:
    return random.choice(AGE_BANDS)

def _diag_list() -> tuple[str, str, str]:
    sample = [random.choice(DIAG_PREFIXES) + str(random.randint(0, 99)) for _ in range(3)]
    return sample[0], sample[1], sample[2]

ROWS = 2000
N_OUT = "data/raw/incoming"

def main() -> None:
    output = Path(__file__).resolve().parent / "synthetic_diabetes.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "encounter_id", "patient_nbr", "race", "gender", "age", "weight",
        "admission_type_id", "discharge_disposition_id", "admission_source_id",
        "time_in_hospital", "payer_code", "medical_specialty",
        "num_lab_procedures", "num_procedures", "num_medications",
        "number_outpatient", "number_emergency", "number_inpatient",
        "diag_1", "diag_2", "diag_3",
        "number_diagnoses",
        "max_glu_serum", "A1Cresult",
        "metformin", "repaglinide", "nateglinide", "chlorpropamide", "glimepiride",
        "acetohexamide", "glipizide", "glyburide", "tolbutamide", "pioglitazone",
        "rosiglitazone", "acarbose", "miglitol", "troglitazone", "tolazamide",
        "examide", "citoglipton", "insulin", "glyburide-metformin",
        "glipizide-metformin", "glimepiride-pioglitazone",
        "metformin-rosiglitazone", "metformin-pioglitazone",
        "change", "diabetesMed", "readmitted",
    ]
    with open(output, "w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(fields)
        rows = []
        # Force a 3-class distribution that includes both "<30" and ">30"
        for i in range(ROWS):
            diag1, diag2, diag3 = _diag_list()
            row = [
                i + 1,
                100000 + (i * 17) % 100000,
                random.choice(["Caucasian", "AfricanAmerican", "Hispanic", "Other"]),
                random.choice(["Male", "Female", "Unknown/Invalid"]),
                _age(),
                "?",
                random.randint(1, 8),
                random.randint(1, 28),
                random.randint(1, 17),
                random.randint(1, 14),
                random.choice(["MC", "BC", "SP", "MD", "WC", "CP"]),
                random.choice(["Cardiology", "InternalMedicine", "Family/GeneralPractice", "Surgery-General"]),
                random.randint(0, 100),
                random.randint(0, 6),
                random.randint(1, 80),
                random.randint(0, 50),
                random.randint(0, 50),
                random.randint(0, 50),
                diag1,
                diag2,
                diag3,
                random.randint(1, 16),
                random.choice(["None", "Norm", ">200", ">300"]),
                random.choice(["None", "Norm", ">7", ">8"]),
            ] + [
                random.choice(["No", "Steady", "Up", "Down"])
                for _ in range(len(fields[24:-3]))
            ] + [
                random.choice(["Ch", "No"]),
                random.choice(["Yes", "No"]),
                # First 200 rows use <30, next 600 use >30, remaining NO
                ("<30" if i < 200 else ">30" if i < 800 else "NO"),
            ]
            rows.append(row)
        writer.writerows(rows)


if __name__ == "__main__":
    main()
