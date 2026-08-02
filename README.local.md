# Local Development & Deployment Guide

This document explains how to run the LifeGuard Readmission Prediction system entirely on your workstation using Docker (no Google Cloud).

## Prerequisites

- Docker Desktop (with Linux containers)
- PowerShell (Windows) or bash (Linux/macOS)
- Node.js and Python are *not* required on the host; the Docker images contain all dependencies.
- The trained model must be present at `ml/models/xgboost_v1/` on the host. If missing, run training first (see below).

---

## Quick Start

1. **Clone the repository** and navigate to the project root.

2. **Install the ML model** (only required once or after model changes):
   ```bash
   # (Optional) create virtualenv and run pipeline to generate model
   # This step requires the raw dataset; it may take several minutes.
   python -m venv .venv
   .venv/bin/activate  # or .venv\Scripts\activate on Windows
   pip install -r ml/requirements.txt
   python ml/run_all.py
   ```
   After this, `ml/models/xgboost_v1/` should contain `model.onnx`, `shap_explainer.pkl`, and `feature_columns.json`.

3. **Start the local stack**:
   ```powershell
   .\scripts\local\run.ps1
   ```
    This builds and starts three containers:
    - PostgreSQL (`db`) on host port **5432**
    - FastAPI backend (`backend`) on host port **8080**
    - Nginx frontend (`frontend`) on host port **8081**

4. **Verify**:
   - Frontend: http://localhost:8081
   - Backend OpenAPI docs: http://localhost:8080/docs
   - Health check: http://localhost:8080/v1/health (should return `{"status":"ok",...}`)
   - Database is reachable on `localhost:5432` with user `lifeguard` / password `lifeguard`.

5. **Stop** the stack:
   ```powershell
   .\scripts\local\stop.ps1
   ```

---

## Architecture

```
┌─────────────────┐     ┌──────────────────┐
│   localhost     │     │    localhost     │
│   port 8081     │────▶│    port 8080     │
└────────┬────────┘     └────────▲─────────┘
         │                      │
         ▼                      │
┌─────────────────┐            │
│  Nginx (frontend)│            │
│  static SPA      │            │
│  proxy /v1/ ->   │────────────┘
│  http://backend:8080  │
└────────▲─────────┘
         │
         │ Docker network
         │
┌────────┴─────────┐
│  FastAPI (backend)│
│  - loads ML model │
│  - PostgreSQL     │
│  - PHI encryption │
└────────▲─────────┘
         │
         ▼
┌─────────────────┐
│   PostgreSQL    │
│   (persisted in │
│   Docker volume)│
└─────────────────┘
```

---

## Configuration

All environment variables are defined in `docker-compose.yml`. Most are fixed for local dev:

- `DATABASE_URL` points to the `db` service.
- `DEV_AUTH_TOKEN` is set to `dev-token-123`. Include header `Authorization: Bearer dev-token-123` for API calls.
- `LOCAL_KEK` provides a deterministic AES key for PHI encryption fallback (not used in dev unless PHI fields are present).
- `CORS_ORIGINS` allows the frontend origin.

To change anything, edit `docker-compose.yml` or rebuild:
```powershell
docker compose build <service>
```

---

## API Usage (examples)

### Health
```bash
curl http://localhost:8080/v1/health
```

### Predict (requires auth)
```bash
curl -X POST http://localhost:8080/v1/predict \
  -H "Authorization: Bearer dev-token-123" \
  -H "Content-Type: application/json" \
  -d '{
    "age": 70,
    "time_in_hospital": 5,
    "num_lab_procedures": 30,
    "num_procedures": 2,
    "num_medications": 10,
    "number_outpatient": 1,
    "number_emergency": 2,
    "number_inpatient": 0,
    "number_diagnoses": 9,
    "max_glu_serum_num": 0,
    "a1c_result_num": 0,
    "gender_male": true,
    "admission_type_emergency": true,
    "discharge_to_home": true,
    "payer_code": "CP",
    "insulin_use": false,
    "metformin_use": true,
    "diabetesMed_yes": true,
    "change_in_meds": false
  }'
```

Replace feature names with those in `ml/data/features/feature_columns.json`. The order matters; the API expects the same order as `feature_columns`.

---

## Database

- The `db` service uses a Docker volume for persistence: `postgres_data`.
- Initial user/password/database are all `lifeguard`.
- Alembic migrations run automatically on backend startup (`MIGRATE_ON_START=1`). Tables are created idempotently.

---

## Notes

- The model is **mounted** from the host (`./ml/models/xgboost_v1`). If you retrain, restart the `backend` container to pick up changes.
- Frontend Nginx proxies `/v1/*` to the backend service.
- All services run in a single Docker network created by Compose; they communicate via service names (`db`, `backend`, `frontend`).
- No PHI is stored in this repository. The `LOCAL_KEK` is a deterministic 32‑byte value for local `AESGCM` encryption; do **not** use it in production.

---

## Troubleshooting

- **Backend fails to start** with `FileNotFoundError` for model: ensure `ml/models/xgboost_v1` exists on host and contains `model.onnx`.
- **Database connection refused**: wait a few seconds after `docker compose up` for Postgres to become ready, or check `docker compose logs db`.
- **Permission denied** on mounted model files (Linux host): adjust file permissions so others can read.
- **Frontend cannot reach backend**: check the `VITE_API_BACKEND` substitution; the Nginx config should show `proxy_pass http://backend:8080;`. You can inspect with `docker exec lifeguard-frontend cat /etc/nginx/conf.d/default.conf`.

---

## Going “cloud‑ready”

When you later move to Google Cloud, the same images can be deployed to Cloud Run. Switch environment variables to use Cloud SQL (via Unix socket or public IP), Cloud KMS, and Secret Manager. The Terraform module under `infra/` already supports that flow.
