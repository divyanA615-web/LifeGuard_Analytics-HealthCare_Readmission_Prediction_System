#!/usr/bin/env bash
# scripts/tunnel/run-tunnel.sh
# Start secure tunnel only after local service is healthy with observable exits

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
CONFIG_FILE="$PROJECT_ROOT/config/tunnel/tunnel-config.ini"

# Load settings
if [[ -f $CONFIG_FILE ]]; then
  export $(grep -v '^#' $CONFIG_FILE | xargs)
fi

cd "$PROJECT_ROOT"

# Dependency pre-check (frugal, no re-install pollution)
command -v cloudflared >/dev/null || { echo "[TUNNEL] cloudflared missing"; exit 1; }
command -v docker >/dev/null || { echo "[TUNNEL] docker required"; exit 1; }
command -v curl >/dev/null || { echo "[TUNNEL] curl needed"; exit 1; }

# 1. ensure compose stack is healthy
docker compose up -d --quiet-pull
until curl -sf http://localhost:8081/healthz >/dev/null; do
  echo "[TUNNEL] waiting on frontend healthz ..."
  sleep 3;
done
until curl -sf http://localhost:8080/v1/health >/dev/null; do
  echo "[TUNNEL] waiting on backend health ..."
  sleep 3;
done
echo "[TUNNEL] services alive — starting tunnel"

# 2. Start boxing according to platform preference
case "${TUNNEL_PLATFORM:-cloudflare}" in
  cloudflare)
    if ! cloudflared tunnel list | grep -q lifeguard-tunnel; then
        echo "[TUNNEL] creating named tunnel: lifeguard-tunnel"
        cloudflared tunnel create lifeguard-tunnel
        cloudflared tunnel route dns lifeguard-tunnel lifeguard-tunnel.example.com
    fi
    echo "[TUNNEL] Running Cloudflare edge-proxied tunnel → backend only"
    cloudflared tunnel --config none --protocol http2 run --url http://localhost:8080 lifeguard-tunnel
    ;;
  ngrok)
    command -v ngrok >/dev/null || { echo "[TUNNEL] ngrok cli missing"; exit 1; }
    echo "[TUNNEL] Running ngrok secure-only tunnel"
    ngrok http 8080 --bind-tls=true | tee tunnel-ngrok.log &
    TUNNEL_PID=$!
    sleep 8
    curl -s http://localhost:4040/api/tunnels | grep -o 'https://[^"]*' | head -1 > logs/tunnel-last.txt
    echo "[TUNNEL] Public URL saved to logs/tunnel-last.txt"
    wait $TUNNEL_PID
    ;;
  *)
    echo "[TUNNEL] Unknown TUNNEL_PLATFORM: ${TUNNEL_PLATFORM}"
    exit 1
    ;;
esac
