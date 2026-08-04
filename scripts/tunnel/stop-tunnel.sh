#!/usr/bin/env bash
# scripts/tunnel/stop-tunnel.sh — graceful teardown (no zombie processes)

set -euo pipefail

echo "[TUNNEL] stopping background daemon..."
if pgrep -f "cloudflared.*lifeguard-tunnel" >/dev/null; then
  echo "[TUNNEL] stopping cloudflared..."
  pkill -f "cloudflared.*lifeguard-tunnel"
elif pgrep -f ngrok >/dev/null; then
  echo "[TUNNEL] stopping ngrok..."
  pkill ngrok || true
fi
rm -f logs/tunnel-last.txt 2>/devnull || true

echo "[TUNNEL] done"
