# Project Makefile (lives at repo root)

ENV ?= dev
PROJECT ?= project-b0677df0-7b67-4302-a4a
REGION ?= asia-south1

.PHONY: lint test format install plan apply

install:
	python -m venv .venv && source .venv/bin/activate && \
	pip install -r ml/requirements.txt && \
	pip install -r backend/requirements.txt

lint:
	cd backend && ruff check app tests
	cd frontend && npm run lint

test:
	pytest ml/tests backend/tests -q

format:
	cd backend && ruff format app tests
	cd frontend && npx prettier --write src

data:
	cd ml && dvc repro

plan:
	cd infra/environments/$(ENV) && terraform plan

apply:
	cd infra/environments/$(ENV) && terraform apply -auto-approve

deploy-api:
	gcloud run deploy $(ENV)-lifeguard-api \
		--image=gcr.io/$(PROJECT)/lifeguard-readmission-api:latest \
		--region=$(REGION) --allow-unauthenticated

deploy-frontend:
	gcloud run deploy $(ENV)-lifeguard-frontend \
		--image=gcr.io/$(PROJECT)/lifeguard-readmission-frontend:latest \
		--region=$(REGION) --allow-unauthenticated

cost-report:
	gcloud billing projects describe $(PROJECT)
