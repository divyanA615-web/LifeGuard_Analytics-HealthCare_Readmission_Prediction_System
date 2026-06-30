# LifeGuard Analytics — Healthcare Readmission Prediction

Production-grade full-stack ML system that predicts 30-day hospital readmission risk
in real time. The model itself is an XGBoost classifier, exported to ONNX for
low-latency CPU inference in Cloud Run. The frontend is React + Vite. ML features
that need an LLM (explanations, similar patient retrieval, dual-models, etc.) are
served by free-tier NVIDIA NIM endpoints.

## Project Structure

```
.
├── backend/          FastAPI service + ONNX inference + NVIDIA proxy
├── frontend/         React + Vite + TypeScript SPA
├── ml/               Data preparation, training, SHAP, DVC pipeline
├── infra/            Terraform infrastructure (GCP, KMS, CMEK, DLP)
├── docs/             Architecture, security, runbook
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

export NVIDIA_API_KEY=nvapi-...          # optional but recommended
export DB_SECRET=<base64-encoded-pg-uri> # set by Terraform deploy

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

- **AES-256-GCM field encryption** via Tink, keys backed by Cloud KMS CMEK
- **De-identification gate** strips all PHI before any NVIDIA API call
- **Append-only audit log** for every prediction (hash-chained in prod)
- **TLS 1.3** enforced end-to-end (HTTPS + Cloud SQL mTLS)
- **OPA policies** ensure every PHI column is encrypted and no public IPs leak
- **Container + IaC scanning** via Trivy, tfsec, checkov

## Cost (Dev)

| Component | Cost / month |
|-----------|--------------|
| Cloud SQL f1-micro | $7 |
| Cloud NAT + DNS | $0.59 |
| Cloud Run (serverless, scale-to-0) | free tier |
| Cloud Storage | free tier |
| NVIDIA free APIs | $0 |
| **Total** | **~$8 / month** |

## License

Apache 2.0 (model) — see `ml/models/MODEL_CARD.md` for the disclaimers
required when reusing the model in clinical practice.
