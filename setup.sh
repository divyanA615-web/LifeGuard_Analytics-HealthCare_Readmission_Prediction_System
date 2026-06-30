#!/usr/bin/env bash
# Complete setup for LifeGuard Readmission Prediction (Linux/macOS)
# Run from the project root: ./setup.sh

set -euo pipefail
echo "=== LifeGuard Setup ==="

echo
echo "[1/5] Creating virtual environment"
python3 -m venv .venv
source .venv/bin/activate
echo "[OK] venv activated"

echo
echo "[2/5] Installing dependencies"
python -m pip install --upgrade pip
python -m pip install -r ml/requirements.txt
python -m pip install -r backend/requirements.txt
echo "[OK] deps installed"

echo
echo "[3/5] Downloading dataset (synthetic fallback)"
python ml/data/make_synthetic_diabetes.py
python ml/data/download_dataset.py --force-synthetic
echo "[OK] dataset ready"

echo
echo "[4/5] Running full ML pipeline"
python ml/run_all.py

echo
echo "[5/5] Done! Pick a step next:"
echo "  - Run the API:  uvicorn app.main:app --reload --port 8080"
echo "  - Run the UI:   cd frontend && npm install && npm run dev"
echo "  - Apply to GCP: cd infra/environments/dev && terraform init && terraform apply"
