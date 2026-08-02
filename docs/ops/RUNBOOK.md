# LifeGuard Operations Runbook (Local & Staging)

## Quick Checks

```powershell
# Validate full system state
./scripts/local/validate.ps1

# Common first 3 lines of troubleshooting:
docker compose logs backend --tail 50
docker compose logs frontend --tail 50
docker compose logs db --tail 50
```

## Escalation Matrix
| Severity | Condition | Commentary | Remedy |
|----------|-----------|------------|--------|
| **P1** | `$env:DATABASE_URL` unset at start | Backend boot loop fails (RuntimeError on import) | Set env before starting; check validate.ps1 FIRST |
| **P1** | Model files absent (`ml/models/xgboost_v1`) | `predict` returns 503 | Run `python ml/run_all.py` to regenerate / mount volume |
| **P2** | Login button loops and never navigates | `frontend/Login.tsx` uses axios; auth endpoint returns JSON but no cookie handling | Cookie now properly set by `set_cookie`; ensure browser allows third-party cookies temporarily (If served on HTTP) |
| **P2** | `Docker engine not running` | Docker Desktop daemon down | Taskbar icon: start Docker Desktop; ensure Linux containers switching done |
| **P3** | Frontend cannot reach backend via `/v1` | Nginx path rewrite misconfigured | Check ` docker exec lifeguard-frontend cat /etc/nginx/conf.d/default.conf` – proxy should point to `http://backend:8080` |
| **Monitoring** | Slow responses (>1s latency) | Model warm-up failed on boot or `uvicorn --workers` misconfigured | Add load test via `locust` in test phase later |

## Security Policy for Local & Production
- **DO NOT** use `localStorage` for PHI tokens. `lifeguard_auth_token` currently stored for header usage... But `/auth/login` now also returns an `HttpOnly` cookie. Frontend should prefer cookies when `SameSite=Strict` is possible and `Secure=true` once TLS enabled.
- **DO NOT** commit `.env` files. Only open `./.env.local` with dev params. Always regenerate `DEV_AUTH_TOKEN` before staging/releases.
- **Audit Chain Verification** (`ml/data/processed/audit_chain.ndjson`): Run `python -m scripts.audit_check` to validate hash-chain continuity before and after new predictions.

## Nut Shell of Agent Outputs
- Every endpoint must return JSON serialized via Pydantic models OR plain strings (validated). No free-text.
- Log formats (configured via logging): `%(asctime)s | %(levelname)s | %(named)s → trace_id`.
- Errors must include `<module>/<function>:<line>`.
- Failure logs reside in logs/runtime/ inside containers. Clusters are removed over DB evacuate.

## Production Checklist Before Leaving Dev
1. Remove dev routes (`/auth/login`) behind flag (`settings.environment in {"prod","staging"}` and return 404).
2. Rotate `DEV_AUTH_TOKEN` and never share it in comments or code. Use `openssl rand -hex 32` to mint a strong token.
3. Convert `docker-compose.yml` → normalized env-specific `docker-compose.{env}.yml` files (for dark secrets).
4. Run `scripts/local/automation/smoke-test.sh` end-to-end pre-push.
