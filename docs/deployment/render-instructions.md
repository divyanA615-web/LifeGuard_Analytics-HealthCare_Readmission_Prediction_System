# Render Deployment Guide — LifeGuard Analytics

This document complements `render.yaml` and provides **step-by-step execution** for
deploying the production-like backend to Render with proper security posture.

> **Zero-Hallucination Requirement**: All steps MUTABLE until verified. Always test locally first:
> ```bash
> docker compose up -d --force-recreate backend
> ```
---

## Pre-flight Security Check

1. **Rotate dev tokens** — replace `local-dev-only-token` used in browser development. Never
   use the same token in production or staging. Use minimum 64-byte hex:
   ```bash
   openssl rand -hex 32
   ```
2. **Enable MFA on the hosting account** (Render supports email + TOTP). Never use plain
   credentials from personal laptops for production deployments.
3. **Verify no hard-coded tokens in output log files:**
   ```bash
   python scripts/secret_scan.py
   ```
   Exit code 0 expected.

---

## Deploy Render Backend

### A. Connect Repository to Render
- In Render Dashboard → **New Web Service**
- Choose **Existing GitHub repository** → `divyanA615-web/LifeGuard_Analytics...`
- Set region `Oregon, US` or whatever nearest your users is
- Dockerfile reference: `./backend/Dockerfile`
- Build command: handled automatically by Dockerfile
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port 10000` (Render defaults to port 10000)

### B. Create Database First
- Azure Postgres `lifeguard-db` can be created before web service to avoid dependency race.
- Record its **Internal Connection String** (`postgresql://...:10000`).

### C. Deploy with Environment Variables (Render Secrets)
| Setting Key | Required | Value Type | Notes |
|-------------|----------|-----------|-------|
| `DATABASE_URL` | YES | Connection string | Injected via Render database link |
| `DEV_AUTH_TOKEN` | YES | Random 64-byte hex | *necessary for login authentication workflow* |
| `MODEL_ARTIFACT_PATH` | YES | `/app/ml/models/xgboost_v1` | Matches our persistent volume path |
| `ENVIRONMENT` | YES | `prod` | Disables dev routes like `/auth/login` when `patch` moved up. **In prod this should be `deny-all` behavior.** |
| `CORS_ORIGINS` | YES | Vercel frontend URL | e.g. `https://myproject.vercel.app` |

---

## Volumes & Storage

- **Persistent Volume** mounted at `/app/ml/models/xgboost_v1` using Render Disk ensures model does not reset across restarts. Without it, the first cold start recreates models (expensive compute time).
- Set `autoBackup=true` in Render volume config if possible.

---

## Test Deployment Endpoints

Once live and certs propagated:

```bash
# Check health (should return {"status":"ok"} with timestamp)
curl https://lifeguard-backend.onrender.com/v1/health

# Login should require valid session management (not built yet in MVP)
curl -X POST https://lifeguard-backend.onrender.com/v1/auth/login \
  -H "Content-Type: application/json"

# Predict should fail without authentication
curl -X POST https://lifeguard-backend.onrender.com/v1/predict \
  -H "Content-Type: application/json" -d '{ ... }'
```

---

## Security Checklist for Production Smoke

- [ ] No HTTP listener enabled (Render provides HTTPS automatically)
- [ ] `ENABLE_HTTPS_REDIRECT=1` not overridden to 0
- [ ] OpenAPI docs (`/v1/docs`) only intranet-only / password protected externally
- [ ] Audit trail hooks verified for `pgcrypto` schema intact on cold start
- [ ] Health endpoint returns timestamp + not-500 backend errors
- [ ] Frontend domain (Vercel) matches Render Service CORS settings exactly

---

## Continuous Deployment & Observability

- **Auto-deploy** stops if you push insecure code. Render pipeline will fail on main branch when health checks timeout.
- **Logs**: Use Render native logging + DataTracer or forward to Sentry using the existing `AGT-08` hooks. Never forward PHI in logs.

---

This file location is phase-a for now — `docs/deployment/render-instructions.md`
