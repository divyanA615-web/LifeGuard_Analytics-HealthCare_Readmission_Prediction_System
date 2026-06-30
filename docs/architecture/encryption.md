# 🛡️ Encryption Architecture

This document is the source of truth for how LifeGuard protects PHI.

## Layers

| Layer | Technology | Description |
|-------|-----------|-------------|
| **Identity** | Cloud IAP + Workload Identity | Authentication at edge |
| **Transport** | TLS 1.3, mTLS to Cloud SQL, HSTS preload | Data in transit |
| **Storage CMEK** | Cloud KMS CMEK for Cloud SQL + GCS | Disk-level encryption at rest (AES-256) |
| **Column** | `phi_encryptor.encrypt_field()` (Tink AEAD) | Per-field AES-256-GCM with AAD |
| **De-ID** | `DeIdentificationGate` → Cloud DLP | Strips PHI before NVIDIA endpoints |
| **Audit** | Append-only NDJSON + Pub/Sub + BigQuery | Hash-chained trail |

## Flow

```
Browser ─ TLS 1.3 ─▶ Cloud Run (FastAPI) ─ mTLS ─▶ Cloud SQL (CMEK)
                                          │
                                          ▼
                                 DeIdentificationGate
                                          │
                                          ▼
                                 NVIDIA NIM endpoint
                                 (no PHI in flight)
```

## Threat Model (STRIDE)

| Threat | Mitigation |
|--------|------------|
| **S**poofing of clinician | IAP JWT signature verification |
| **T**ampering of audit log | Hash-chained entries, appended-only RLS policy |
| **R**epudiation of prediction | Audit log per-prediction, immutable |
| **I**nformation disclosure | PHI AES-256-GCM, Cloud DLP pre-NVIDIA |
| **D**enial of service | Cloud Run max-instance + Cloud Armor WAF |
| **E**levation of privilege | Workload Identity (no static keys), IAM least privilege |

## Rotation

Cloud KMS rotation period: **90 days**.
A failure to rotate triggers a Slack alert via `infra/modules/cloud-run/main.tf`.

## Implementation Hooks

* `backend/app/security/phi_encryptor.py` – Tink AEAD primitives
* `backend/app/security/deid_gate.py` – DLP + tokenized stripping
* `backend/app/security/audit_logger.py` – Append-only audit chain
* `infra/modules/cloud-kms/main.tf` – CMEK + rotation
* `infra/policies/conftest.rego` – OPA enforcement
