# Security Policy — LifeGuard Readmission Prediction System

## Scope

This repository ships **only synthetic and publicly-de-identified datasets**.
It is a code-only artifact comprising:

* FastAPI backend with AES‑256‑GCM PHI encryption + Cloud DLP de‑identification
* ONNX-based XGBoost classifier + SHAP explainer
* React + Vite + MUI clinical frontend
* Terraform infrastructure for GCP (CMEK, audit sink, Cloud Run, Cloud SQL)
* NVIDIA build.nvidia.com free-tier wrappers (de-identified payloads only)

The repository **must not contain real patient PHI**. Any leak of personal
data, secrets, API keys, or proprietary healthcare records is an incident.

## Supported versions

| Branch   | Supported |
|----------|-----------|
| `main`   | ✅ Yes    |
| any other| ❌ No     |

## Reporting a vulnerability

* **Do not file a public issue.**
* Email the maintainer at `security@lifeguard.example` (PGP key on request).
* Subject prefix: `[SECURITY] <short description>`.
* Expected acknowledgement: 2 business days.
* Expected fix or mitigation plan: 7 business days.

Encrypted transport is appreciated; a temporary PSST/Ticket system may be
offered for exceptionally sensitive disclosures.

## What we promise

* We will not disclose any details of your report beyond the small triage
  team until after a patch or workaround is published.
* We will credit you in the release notes at your preference
  (`anonymous`, `handle`, or `real name`).
* We follow **Coordinated Disclosure** with a typical 90-day window before
  public disclosure.

## What is in scope

| In scope for bounty/first-response | Excluded (use normal support) |
|------------------------------------|-------------------------------|
| ONNX inference path                | Feature requests              |
| PHI encrypt/decrypt AAD misuse      | Documentation typos            |
| Audit hash chain bypass            | Demo deployment misuses        |
| Token de-identification leaks      | Vendor issues (NVIDIA / GCP)   |
| Terraform IAM over-permissive roles| Performance tuning             |
| Auth header bypass                 | User UX complaints            |
| Secret mishandling / key rotation  |                              |

## Hardening controls already implemented

| Layer | Control | File |
|------|---------|------|
| Transport | TLS 1.3 + HSTS preload | `backend/app/main.py`, `frontend/nginx.conf` |
| Storage | Cloud KMS CMEK (90-day rotation) | `infra/modules/cloud-kms/main.tf` |
| Field-level | AES-256-GCM with AAD | `backend/app/security/phi_encryptor.py` |
| De-identification | Cloud DLP pre-NVIDIA API | `backend/app/security/deid_gate.py` |
| Auth | Cloud IAP + JWT validation | `backend/app/security/auth_middleware.py` |
| Audit | Hash-chained, append-only NDJSON | `backend/app/security/audit_logger.py` |
| IaC | OPA policies (no public IPs, CMEK-only) | `infra/policies/conftest.rego` |
| Container | Trivy in CI | `.github/workflows/security-scan.yml` |
| Secret | `gitleaks` patterns in CI | `.github/workflows/security-scan.yml` |

## Operations notes

* Rotate the **GH_PAT** token in GitHub settings after the initial push — see
  `docs/runbook/deploy.md` for a 90-day rotation procedure.
* Never store Kaggle credentials inside the repository; load via env vars.
* When onboarding a real hospital CE, **revoke the public build pipeline
  PAT** and bind CI to a per-environment EID (CI service account).
