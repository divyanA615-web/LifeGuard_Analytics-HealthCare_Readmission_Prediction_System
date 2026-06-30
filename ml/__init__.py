"""Project-wide constants for LifeGuard Readmission Prediction."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ML_ROOT = PROJECT_ROOT / "ml"

DATA_RAW = ML_ROOT / "data" / "raw"
DATA_PROCESSED = ML_ROOT / "data" / "processed"
DATA_FEATURES = ML_ROOT / "data" / "features"
MODELS_DIR = ML_ROOT / "models"
NOTEBOOKS_DIR = ML_ROOT / "notebooks"

RANDOM_SEED = 42
TEST_SIZE = 0.20
TRAIN_VAL_TEST_SPLIT = (0.7, 0.15, 0.15)

DIABETES_KAGGLE_SLUG = "brandao/diabetes"
DIABETES_FILENAME = "diabetic_data.csv"
MAPPING_FILENAME = "IDS_mapping.csv"

TARGET_COLUMN = "readmitted_30d"
PATIENT_ID_COLUMN = "patient_token"
TIMESTAMP_COLUMN = "encounter_date"

NUMERIC_FEATURES = [
    "age",
    "time_in_hospital",
    "num_lab_procedures",
    "num_procedures",
    "num_medications",
    "number_outpatient",
    "number_emergency",
    "number_inpatient",
    "number_diagnoses",
    "max_glu_serum_num",
    "a1c_result_num",
]

CATEGORICAL_FEATURES = [
    "gender_male",
    "admission_type_emergency",
    "discharge_to_home",
    "payer_code",
    "insulin_use",
    "metformin_use",
    "diabetesMed_yes",
    "change_in_meds",
]

EHR_TABLES = ["admissions", "patients", "diagnoses_icd", "labevents", "prescriptions"]

CLOUD_CONFIG = {
    "project_id": "project-b0677df0-7b67-4302-a4a",
    "region": "asia-south1",
    "zone": "asia-south1-a",
    "state_bucket": "lifeguard-tf-state",
    "model_bucket_name": "lifeguard-models-dev",
}

__all__ = [
    "PROJECT_ROOT", "ML_ROOT", "DATA_RAW", "DATA_PROCESSED",
    "DATA_FEATURES", "MODELS_DIR", "NOTEBOOKS_DIR",
    "RANDOM_SEED", "TEST_SIZE", "TRAIN_VAL_TEST_SPLIT",
    "DIABETES_KAGGLE_SLUG", "DIABETES_FILENAME", "MAPPING_FILENAME",
    "TARGET_COLUMN", "PATIENT_ID_COLUMN", "TIMESTAMP_COLUMN",
    "NUMERIC_FEATURES", "CATEGORICAL_FEATURES",
    "EHR_TABLES", "CLOUD_CONFIG",
]
