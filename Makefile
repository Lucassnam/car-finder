# Car Finder — convenience targets (macOS/Linux). On Windows use the .ps1 scripts.
.PHONY: help setup models db-up db-down backend frontend

help:                ## show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  %-10s %s\n", $$1, $$2}'

setup:               ## one-shot install of everything
	bash scripts/setup.sh

models:              ## pull/refresh the Ollama models
	bash scripts/pull-models.sh

db-up:               ## start Postgres+PostGIS
	docker compose up -d db

db-down:             ## stop Postgres
	docker compose down

migrate:             ## run Alembic migrations (run once after setup)
	cd backend && ../.venv/bin/alembic upgrade head || backend/.venv/bin/alembic upgrade head

backend:             ## run the API
	backend/.venv/bin/uvicorn app.main:app --reload --app-dir backend

frontend:            ## run the dashboard
	cd frontend && npm run dev
