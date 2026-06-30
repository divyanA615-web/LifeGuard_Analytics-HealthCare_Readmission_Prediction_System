# PHI Fields Inventory

This document enumerates every PHI field handled by the LifeGuard platform.
Each row identifies both the source and the encryption strategy applied.

| Column / Field | Source | Encrypted at rest | Strategy |
|----------------|--------|-------------------|----------|
| `patient_name` | Encrypted by backend on ingest | ✓ | `phi_encryptor.encrypt_field("patient_name")` (AES-256-GCM) |
| `mrn` | Stored as ciphertext | ✓ | `phi_encryptor.encrypt_field("mrn")` |
| `ssn` | Stored as ciphertext | ✓ | `phi_encryptor.encrypt_field("ssn")` |
| `dob` | Stored as ciphertext | ✓ | `phi_encryptor.encrypt_field("dob")` |
| `address` | Stored as ciphertext | ✓ | `phi_encryptor.encrypt_field("address")` |
| `phone` | Stored as ciphertext | ✓ | `phi_encryptor.encrypt_field("phone")` |
| `email` | Stored as ciphertext | ✓ | `phi_encryptor.encrypt_field("email")` |
| `attending_physician` | Stored as ciphertext | ✓ | `phi_encryptor.encrypt_field("attending_physician")` |
| Free-text clinical notes | Stored as ciphertext | ✓ | `phi_encryptor.encrypt_field("note")` |
| `patient_token` | Derived from encounter_id | n/a (already pseudonymous) | SHA-256 with secret salt |

## Non-PHI fields used for ML

The following columns are used by the XGBoost model. They are derived from
de-identified records and contain no patient identifiers.

```
age, time_in_hospital, num_lab_procedures, num_procedures, num_medications,
number_outpatient, number_emergency, number_inpatient, number_diagnoses,
max_glu_serum_num, a1c_result_num, gender_male, admission_type_emergency,
discharge_to_home, payer_code, insulin_use, metformin_use, diabetesMed_yes,
change_in_meds
```

## De-identification Gate

Every outbound payload to a NVIDIA endpoint passes through
`DeIdentificationGate.prepare_payload()`, which:

1. Strips PHI fields listed above
2. Replaces them with deterministic tokens
3. Inspects the resulting payload with Cloud DLP for residual PHI
4. Raises `PHILeakError` on detection (monitoring alert triggered)

## Audit Trail

Every PHI read/write goes through `AuditLogger.emit()` which:

1. Appends an audit record to hash-chained NDJSON file
2. Publishes the record's hash to Pub/Sub (BigQuery sink)
3. Records who, what, when, and which patient was touched
