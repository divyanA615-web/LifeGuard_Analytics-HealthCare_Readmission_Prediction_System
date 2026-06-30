# 🏗️ System Architecture

## Request Flow

```
Browser                       Cloud Run (API)                 Cloud SQL
───────                       ──────────────                  ─────────
[1] Login (IAP)
       │
       ▼
[2] Patient intake (TLS 1.3)
   │
   ▼
[3] Predict ──────────▶ [Login → Auth]
                         [Load feature_columns.json]
                         [ONNX inference (CPU)]
                         [SHAP tree explainer]
                         [De-ID gate]
                         [NVIDIA Nemotron LLM]
                         [Persist prediction]
                         [Audit log + chain]   ──────▶ [Cloud SQL]
                                                              │
                                                              ▼
                                                       [Append-only audit]
```

## Key Components

* `backend/app/main.py` – FastAPI entry, lifespan warm-up
* `backend/app/ml/pipeline.py` – bridges inference + SHAP
* `backend/app/security/` – encryption, de-ID, audit
* `ml/` – DVC pipeline, ONNX artefacts
* `frontend/src/` – React + MUI; Cloud IAP login uses Google OAuth

## Cost Heatmap

| Region        | SKU              | Cost / month |
| ------------- | ---------------- | ------------ |
| asia-south1   | Cloud SQL f1     | $7           |
| asia-south1   | Cloud NAT egress | $0.5         |
| asia-south1   | Cloud Run min=0  | $0 (free)    |
| NVIDIA        | Free tier        | $0           |
| **Total dev** |                  | **~$8**      |

## SLOs

* p95 prediction latency < 300 ms
* availability 99.5% (dev) / 99.9% (prod)
* prediction success rate > 99%
