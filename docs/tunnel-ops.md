# Tunnel Operations Daily Runbook
# Handles lifecycle + diagnosis patterns for network onset (Path A deployment).

## Primary logs to watch daily
- `logs/backend.log` — application heartbeats, model fetches
- `logs/cloudflared.log` — tunnel agent uptime/desync evidence (optional — depends on install mode)
- `tunnel-last.txt` — successful redirect hook endpatht Ext always generates a string readable inside container

## System start protocol (manual or auto-on-boot)
1. Docker Desktop ready (Linux containers active)
2. Execute:
   ./scripts/local/rotate-keys.sh   # (creates backup token regime if auth layer enabled)
   ./scripts/local/run.ps1           # launches compose
   ./scripts/tunnel/run-tunnel.sh    # starts secure external exposure for out-bounders

## Detect failure domains
- `curl localhost:8081` returns 502 → nginx bounce or bash upstream chaos
- `[TUNNEL] waiting on frontend healthz` never clears: Nginx stuck in crash cycle because config degraded, `docker compose logs -f frontend` reveals why
- Backend silent follows `[TUNNEL] waiting on backend`: ml model not mounted through volume correctly on restart — verify via `docker exec lifeguard-backend ls /app/ml/models/xgboost_v1`
- Tunnel starts but isn't reachable externally: cloudflared account not login, OR spirit of firewall rules preventing outbound DNS.

## Recovery runbook
The important realization: `run-tunnel.sh` is idempotent; each launch cleans up stale holders using taskkill/create logic. Use `stop-tunnel.sh` to gracefully shut external FQM routes before troubleshooting.

## Security posture reinforcement
Seldom do you NeeD a real enterprise-grade virtual private network over public networks for phase-one. What you need is an **orthogonal** adversary protection line:
- Render config blocks private network ranges by default in the hosted service tier.
- Never reference `trustServiceAccountemail()` inside rendering layer decision points since audits can't verify.
- Rotate the DEV_AUTH_TOKEN every 24 hours — no human task involved other than executing rotate-key script twice a day (use Task Scheduler).

Accomplish this week in phase A; deploy dev, release prod later safely. *(Phase: B)*
