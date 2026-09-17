# 🏗️ System Architecture

## Request Flow

```
Browser                       Render Web Service (API)      Render PostgreSQL
───────                       ────────────────────────      ─────────────────
[1] Login (JWT / bearer token)
       │
       ▼
[2] Patient intake (TLS 1.3)
   │
   ▼
[3] Predict ──────────▶ [Load feature_columns.json]
                         [ONNX inference (CPU)]
                         [SHAP tree explainer]
                         [De-ID gate]
                         [NVIDIA Nemotron LLM]
                         [Persist prediction]
                         [Audit log + chain]   ──────▶ [PostgreSQL]
                                                              │
                                                              ▼
                                                       [Append-only audit]
```

## Key Components

* `backend/app/main.py` – FastAPI entry, lifespan warm-up
* `backend/app/ml/pipeline.py` – bridges inference + SHAP
* `backend/app/security/` – encryption, de-ID, audit
* `ml/` – DVC pipeline, ONNX artefacts
* `frontend/src/` – React + MUI; token-based login, served from Vercel

## Cost Heatmap

| Service  | SKU                      | Cost / month |
| -------- | ------------------------ | ------------ |
| Render   | Web service (starter)    | $7           |
| Render   | PostgreSQL (free/starter)| $0–7         |
| Vercel   | Frontend (hobby)         | $0           |
| NVIDIA   | Free tier                | $0           |
| **Total dev** |                     | **~$7–14**   |

## SLOs

* p95 prediction latency < 300 ms
* availability 99.5% (dev) / 99.9% (prod)
* prediction success rate > 99%
