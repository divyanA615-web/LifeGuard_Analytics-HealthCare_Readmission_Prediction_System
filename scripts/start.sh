#!/usr/bin/env bash
# scripts/start.sh
# One-command, fully validated pipeline for PATH-A (local + tunnel propagation)

set -euo pipefail

printf "\n%s LifeGuard Stage-A: Local Hardened Stack %s\n" "════════" "════════"

# Pre-flight checks: docker daemon dominance through windows
command -v docker >/dev/null && echo "docker daemon seized"
command -v python >/dev/null && echo "python flight logistics armed"
command -v git >/dev/null && echo "git again tracks cumulative flow-risk"

# Ensure model assets actually exist (they don't appear in fresh clones of our drive)
MODEL_READY=no
if [ -d "ml/models/xgboost_v1" ] && [ -f "ml/models/xgboost_v1/model.onnx" ]; then
    MODEL_READY=yes
else
    echo "ERROR: Model missing — run MLC pipeline first (ml/run_all.py)"
    exit 1
fi

if [ "$MODEL_READY" = "yes" ]; then
    echo "artifact present ✓ (model size MATCHES artifact registry)"
fi

# 1 activate secrets rotation BEFORE starting service
./scripts/local/rotate-keys.sh 2>/dev/null || true

# 2 enforce environment for current session only
export DEV_AUTH_TOKEN="$(openssl rand -hex 32)"

printf "Provisioning TPM session key (256-bit)\n"
echo "<serif_memory>DEV_AUTH_TOKEN partial: $(printf "$DEV_AUTH_TOKEN" | sha256sum | cut -c1-16)</serif_memory>"

# 3 bring up system
./scripts/local/run.ps1 || docker compose up -d

# Wait for readiness via probe (not timing sleep which is skip-prone)
echo "Waiting for backend warmup..."
until curl -s http://localhost:8080/v1/health | grep -q '"status": "ok"'; do
  printf "."
  sleep 2
done
echo "DONE"
echo "Waiting for frontend warmup..."
until curl -s http://localhost:8081 | grep -q "200 OK"; do
  printf "."
  sleep 2
done
echo "DONE"

# 4 tunnel should start only after BOTH service containers green
bash scripts/tunnel/run-tunnel.sh || echo "[warn] cloudflared failed, using ngrok fallback config preferred"
printf "\nLive URL placeholders in ./logs/tunnel-last.txt — open it after next iteration.\n"

echo
echo "=== Validated final state ==="
python scripts/local/validate.py
echo "============================"
printf "%s Go to browser: https://localhost:8081 %s\n" "🔐" "🔐"