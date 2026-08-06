# deploy-vercel.ps1 — Deploy LifeGuard frontend to Vercel from Windows PowerShell
# Usage:  .\scripts\deploy\deploy-vercel.ps1
# Requires: Node 20+, `npm i -g vercel`, and `vercel login` already done one time.

$ErrorActionPreference = "Stop"

Set-Location (Join-Path $PSScriptRoot "..\..\frontend")

Write-Host "== LifeGuard Vercel Deployment ==" -ForegroundColor Cyan

# 1. Local gate: typecheck + build must pass before cloud upload
npm ci --no-audit --no-fund
npm run typecheck
npm run build
if ($LASTEXITCODE -ne 0) { Write-Host "Build failed — not deploying" -ForegroundColor Red; exit 1 }

# 2. Backend URL must be known at build time
$backend = Read-Host "Enter backend URL (e.g. https://lifeguard-backend.onrender.com/v1)"
if (-not $backend.StartsWith("https://")) { Write-Host "Must be https URL" -ForegroundColor Red; exit 1 }

# 3. Deploy with the env var set for this build
$env:VITE_API_BASE = $backend
vercel --prod --yes

Write-Host ""
Write-Host "Deployed. Smoke test:" -ForegroundColor Green
Write-Host "  1. Open your Vercel URL → /login → click Sign in"
Write-Host "  2. Expected: SPA loads, login POST reaches Render backend"
Write-Host "  3. If login fails: check Render env CORS_ORIGINS includes your Vercel domain"
