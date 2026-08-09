# deploy-render.ps1 — Deploy LifeGuard backend to Render from Windows PowerShell
# Usage:  .\scripts\deploy\deploy-render.ps1
# Requires: GitHub repo linked to Render (Dashboard → New → Blueprint), or Render CLI configured.

$ErrorActionPreference = "Stop"

Write-Host "== LifeGuard Render Deployment ==" -ForegroundColor Cyan

# 1. Sanity: render.yaml parses
python -c "import yaml,sys; yaml.safe_load(open('render.yaml')); print('render.yaml OK')"

# 2. Sanity: secrets NOT committed anywhere tracked
$bad = git grep -nI "openssl rand" -- . 2>$null | Where-Object { $_ -notmatch "render.yaml|docs/" }
if ($bad) { Write-Host "Secret-pattern leak risk:" -ForegroundColor Red; $bad; exit 1 }

# Step 3: Generate fresh production values (rotate immediately after first deploy)
$kek = -join ((1..64) | ForEach-Object { '{0:x}' -f (Get-Random -Max 16) })
$authToken = -join ((1..32) | ForEach-Object { '{0:x}' -f (Get-Random -Max 16) })

@"
Render Frontend Environment Variables (paste into Settings → Environment):
────────────────────────────────────────────────────────────────────────────
DEV_AUTH_TOKEN = $authToken
LOCAL_KEK      = $kek
CORS_ORIGINS   = https://<your-vercel-project>.vercel.app   (fill after Vercel deploy)
"servicesHostname" from Render is typically: https://lifeguard-backend.onrender.com
────────────────────────────────────────────────────────────────────────────
These values are one-time use; rotate via the Render dashboard after deploy.
"@ | Out-File docs/deployment/render-secrets.txt -Encoding utf8

Write-Host "`nSecrets written to docs/deployment/render-secrets.txt" -ForegroundColor Green

Write-Host ""
Write-Host "Paste these into Render → lifeguard-backend → Environment (ONE TIME, then rotate)" -ForegroundColor Yellow
Write-Host "LOCAL_KEK      = $kek"
Write-Host "DEV_AUTH_TOKEN = $devToken"
Write-Host "CORS_ORIGINS   = https://<your-vercel-project>.vercel.app  (fill after Vercel step)"
Write-Host ""
Write-Host "== Next ==" -ForegroundColor Cyan
Write-Host "1. Push this commit:            git push origin main"
Write-Host "2. Render Dashboard:            New → Blueprint → pick this repo (it reads render.yaml)"
Write-Host "3. Wait for DB + web service to create; fill the sync:false env vars above"
Write-Host "4. Check health:                curl https://lifeguard-backend.onrender.com/v1/health"
