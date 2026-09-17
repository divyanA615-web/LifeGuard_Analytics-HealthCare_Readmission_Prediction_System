# 🛡️ Encryption Architecture

This document is the source of truth for how LifeGuard protects PHI.

## Layers

| Layer | Technology | Description |
|-------|-----------|-------------|
| **Identity** | JWT (ES256) bearer token / dev token | Authentication at the FastAPI edge |
| **Transport** | TLS 1.3 (Render-managed) + HSTS preload | Data in transit |
| **Database** | Render PostgreSQL (TLS-managed) | Encrypted at rest by provider |
| **Column** | `phi_encryptor.encrypt_field()` (Tink AEAD) | Per-field AES-256-GCM with AAD |
| **De-ID** | `DeIdentificationGate` (regex + tokenize) | Strips PHI before NVIDIA endpoints |
| **Audit** | Append-only NDJSON hash-chain | Tamper-evident trail |

## Flow

```
Browser ─ TLS 1.3 ─▶ Vercel (React) ─ TLS 1.3 ─▶ Render (FastAPI)
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
| **S**poofing of clinician | JWT signature verification + expiry |
| **T**ampering of audit log | Hash-chained NDJSON entries |
| **R**epudiation of prediction | Audit log per-prediction, immutable |
| **I**nformation disclosure | PHI AES-256-GCM, De-ID gate pre-NVIDIA |
| **D**enial of service | Render DDoS mitigation + free-tier NVIDIA rate limit |
| **E**levation of privilege | Per-role JWT claims (`clinician`, `admin`) |

## Rotation

Field-encryption KEK (`LOCAL_KEK` env var) rotation: **90 days**.
Rotate by generating a new secret and redeploying from the Render dashboard.

## Implementation Hooks

* `backend/app/security/phi_encryptor.py` – Tink AEAD primitives
* `backend/app/security/deid_gate.py` – regex + tokenized stripping
* `backend/app/security/audit_logger.py` – Append-only audit chain
* `backend/app/security/key_rotation.py` – rotation helper
