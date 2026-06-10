#!/usr/bin/env bash
# Car Finder — one-shot setup for macOS / Linux (your DEV machine)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$SCRIPT_DIR")"
cd "$ROOT"

echo "▶ Car Finder — macOS/Linux setup"

# 1. System prerequisites via Homebrew ----------------------------------------
if ! command -v brew >/dev/null 2>&1; then
  echo "✖ Homebrew not found. Install it first:  https://brew.sh"
  exit 1
fi
echo "▶ Installing system tools (git, python@3.12, node, ollama, docker)…"
brew install git python@3.12 node ollama
brew install --cask docker || echo "  (Docker Desktop cask may already be installed — continuing)"

# 2. Python backend -----------------------------------------------------------
echo "▶ Setting up Python backend in backend/.venv …"
python3.12 -m venv backend/.venv
# shellcheck disable=SC1091
source backend/.venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt
python -m playwright install chromium

# 3. Frontend -----------------------------------------------------------------
echo "▶ Installing frontend deps…"
( cd frontend && npm install )

# 4. Env file -----------------------------------------------------------------
[ -f .env ] || { cp .env.example .env; echo "▶ Created .env from template"; }

# 5. Database -----------------------------------------------------------------
echo "▶ Starting Postgres+PostGIS (Docker must be running)…"
docker compose up -d db

# 6. AI models ----------------------------------------------------------------
echo "▶ Pulling local AI models (downloads several GB)…"
bash scripts/pull-models.sh

# 7. Database migrations -------------------------------------------------------
echo "▶ Running database migrations…"
sleep 3  # give Postgres a moment to fully start
( cd backend && .venv/bin/alembic upgrade head )

echo ""
echo "✓ Setup complete. Next: see SETUP.md → 'Running it'."
echo "  make backend   →  http://localhost:8000"
echo "  make frontend  →  http://localhost:3000"
