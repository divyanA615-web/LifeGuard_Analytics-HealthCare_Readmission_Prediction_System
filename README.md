# LifeGuard Analytics — Healthcare Readmission Prediction

> ⚠️ **No PHI in this repository.** This codebase ships with **synthetic** and
> **publicly-de-identified** data only — currently the UCI Diabetes
> 130-US Hospitals benchmark (CC0/CC-BY, already de-identified per
> 45 CFR §164.514 Safe Harbor) and procedurally-generated Synthea-style
> records. **Real patient identifiers, credentials, or production
> data of any kind must never be committed to any branch.**
>
> Production deployment of real patient data requires a Business Associate
> Agreement (BAA) with a hospital Covered Entity plus downstream BAAs
> with the cloud and AI providers. See `SECURITY.md` for the responsible
> disclosure policy and `docs/security/incident_response.md` for the
> HIPAA-readiness checklist.

Production-grade full-stack ML system that predicts 30-day hospital readmission risk
in real time. The model itself is an XGBoost classifier, exported to ONNX for
low-latency CPU inference in a Render web service. The frontend is React + Vite
hosted on Vercel. ML features that need an LLM (explanations, similar patient
retrieval, dual-models, etc.) are served by free-tier NVIDIA NIM endpoints.

## Project Structure

```
.
├── backend/          FastAPI service + ONNX inference + NVIDIA proxy
├── frontend/         React + Vite + TypeScript SPA (Vercel)
├── ml/               Data preparation, training, SHAP, DVC pipeline
├── docs/             Architecture, security, runbook
├── render.yaml       Render blueprint (backend + PostgreSQL)
└── .github/          CI/CD workflows
```

## Datasets (No BAA required for local/dev use)

1. **Diabetes 130-US Hospitals** (Kaggle, no credential) — primary dataset
   Download from <https://www.kaggle.com/datasets/brandao/diabetes>
   Place the CSV at `ml/data/raw/diabetic_data.csv`.

2. **Synthea** (synthetic FHIR; install locally if you want unlimited training data)
3. **MIMIC-IV** (requires PhysioNet CITI training; optional)

## Quick Start — Data & Training

```bash
# Install Python deps (use a venv)
python -m venv .venv && source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r ml/requirements.txt

# Place or download the Diabetes CSV
kaggle datasets download -d brandao/diabetes -p ml/data/raw --unzip

# Run the entire DVC pipeline (prepare → split → features → train → evaluate)
pip install dvc[ml]
dvc repro
```

After training completes the artefacts live at:

```
ml/data/processed/diabetes_readmission.parquet
ml/data/splits/{train,val,test}.parquet
ml/data/features/{scaler.pkl, feature_columns.json, *_X.parquet}
ml/models/xgboost_v1/{model.json, model.onnx, shap_explainer.pkl}
ml/metrics/{training.json, evaluation.json}
```

## Quick Start — Backend

```bash
cd backend
pip install -r requirements.txt

export NVIDIA_API_KEY=nvapi-...       # optional but recommended
export DATABASE_URL=postgres://...    # from Render dashboard

uvicorn app.main:app --host 0.0.0.0 --port 8080
```

The API exposes:

- `POST /v1/predict` — synchronous real-time inference
- `POST /v1/predict/batch` — batch scoring (used by triage dashboards)
- `GET /v1/patients/{token}/history` — encrypted history viewer
- `POST /v1/feedback` — clinician feedback loop
- `GET /v1/health` — tap for liveness/readiness probes

## Quick Start — Frontend

```bash
cd frontend
npm install
npm run dev
```

Open <http://localhost:5173> for the patient-facing SPA.

## Security Highlights

- **AES-256-GCM field encryption** via Tink, key from `LOCAL_KEK` env var
- **De-identification gate** strips all PHI before any NVIDIA API call
- **Append-only audit log** for every prediction (hash-chained)
- **TLS 1.3** enforced end-to-end (Vercel + Render edge TLS)
- **Container scanning** via Trivy (HIGH/CRITICAL gate on every push)

## Cost (Dev)

| Component | Cost / month |
|-----------|--------------|
| Render web service (starter) | $7 |
| Render PostgreSQL | $0–7 |
| Vercel (frontend) | $0 (hobby) |
| NVIDIA free APIs | $0 |
| **Total** | **~$7–14 / month** |

## License

Apache 2.0 (model) — see `ml/models/MODEL_CARD.md` for the disclaimers
required when reusing the model in clinical practice.
