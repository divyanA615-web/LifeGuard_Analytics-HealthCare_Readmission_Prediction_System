# Requires Docker Desktop (Windows)
cd $PSScriptRoot/../..
Write-Host "Building images..."
docker compose build --no-cache
Write-Host "Starting services..."
docker compose up -d
Write-Host "Waiting for backend health..."
timeout /t 10
docker compose ps
Write-Host "`nFrontend: http://localhost:3000"
Write-Host "Backend docs: http://localhost:8080/docs"
Write-Host "API health: http://localhost:8080/v1/health"