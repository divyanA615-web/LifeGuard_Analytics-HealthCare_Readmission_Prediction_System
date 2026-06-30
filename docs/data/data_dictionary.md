# Data Dictionary

| Table | Column | Type | Description | PHI? |
|-------|--------|------|-------------|------|
| `patients` | `id` | BIGSERIAL | PK | no |
| `patients` | `patient_token` | VARCHAR(64) | Pseudonymous key | no |
| `patients` | `ssn_enc` | TEXT | Encrypted PHI | yes |
| `patients` | `mrn_enc` | TEXT | Encrypted PHI | yes |
| `patients` | `name_enc` | TEXT | Encrypted PHI | yes |
| `patients` | `dob_enc` | TEXT | Encrypted PHI | yes |
| `patients` | `age_band` | VARCHAR(8) | Quintile band | no |
| `patients` | `gender` | VARCHAR(8) | self-reported | no |
| `predictions` | `id` | BIGSERIAL | PK | no |
| `predictions` | `patient_token` | VARCHAR(64) | FK by token | no |
| `predictions` | `model_version` | VARCHAR(32) | model tag | no |
| `predictions` | `risk_proba` | FLOAT | 0.0..1.0 | no |
| `predictions` | `risk_label` | VARCHAR(16) | LOW/MED/HIGH | no |
| `predictions` | `features_json` | JSONB | non-PHI features | no |
| `predictions` | `explanation_json` | JSONB | SHAP list | no |
| `predictions` | `clinician_id` | VARCHAR(64) | IAP sub | no |
| `predictions` | `actor_email` | VARCHAR(120) | from IAP | no |
| `predictions` | `created_at` | TIMESTAMP | | no |
| `feedback` | `prediction_id` | BIGINT | FK | no |
| `feedback` | `clinician_id` | VARCHAR(64) | IAP sub | no |
| `feedback` | `actual_readmitted_30d` | BOOLEAN | ground truth | no |
| `feedback` | `clinician_notes_enc` | TEXT | Encrypted PHI | yes |
| `audit_entries` | `id` | BIGSERIAL | PK | no |
| `audit_entries` | `actor` | VARCHAR(120) | who | no |
| `audit_entries` | `action` | VARCHAR(64) | login/predict/feedback | no |
| `audit_entries` | `target` | VARCHAR(120) | resource id | no |
| `audit_entries` | `payload_json` | JSONB | metadata | no |
| `audit_entries` | `prev_hash` | VARCHAR(64) | chain link | no |
| `audit_entries` | `chain_hash` | VARCHAR(64) | sha256 | no |
