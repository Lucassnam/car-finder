# Car Finder — one-shot setup for Windows (your 5080 PC / PROD machine)
# Run in PowerShell:  .\scripts\setup.ps1
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "Car Finder — Windows setup" -ForegroundColor Cyan

function Ensure-Winget($id, $name) {
  Write-Host ">> Installing $name ..." -ForegroundColor Cyan
  winget install --id $id -e --accept-source-agreements --accept-package-agreements --silent
  # winget returns non-zero when already installed; that's fine, keep going.
}

# 1. System prerequisites -----------------------------------------------------
Ensure-Winget "Git.Git"              "Git"
Ensure-Winget "Python.Python.3.12"   "Python 3.12"
Ensure-Winget "OpenJS.NodeJS.LTS"    "Node.js LTS"
Ensure-Winget "Docker.DockerDesktop" "Docker Desktop"
Ensure-Winget "Ollama.Ollama"        "Ollama"

Write-Host "NOTE: if any tool was freshly installed, close & reopen PowerShell so PATH updates, then re-run this script." -ForegroundColor Yellow

# 2. Python backend -----------------------------------------------------------
Write-Host ">> Setting up Python backend in backend\.venv ..." -ForegroundColor Cyan
py -3.12 -m venv backend\.venv
backend\.venv\Scripts\python.exe -m pip install --upgrade pip
backend\.venv\Scripts\pip.exe install -r backend\requirements.txt
backend\.venv\Scripts\python.exe -m playwright install chromium

# 3. Frontend -----------------------------------------------------------------
Write-Host ">> Installing frontend deps ..." -ForegroundColor Cyan
Push-Location frontend
npm install
Pop-Location

# 4. Env file -----------------------------------------------------------------
if (-not (Test-Path ".env")) { Copy-Item ".env.example" ".env"; Write-Host ">> Created .env from template" }

# 5. Database -----------------------------------------------------------------
Write-Host ">> Starting Postgres+PostGIS (make sure Docker Desktop is running) ..." -ForegroundColor Cyan
docker compose up -d db

# 6. AI models ----------------------------------------------------------------
Write-Host ">> Pulling local AI models (downloads several GB) ..." -ForegroundColor Cyan
& "$PSScriptRoot\pull-models.ps1"

# 7. Database migrations -------------------------------------------------------
Write-Host ">> Running database migrations ..." -ForegroundColor Cyan
Start-Sleep -Seconds 3
Push-Location backend
backend\.venv\Scripts\alembic.exe upgrade head
Pop-Location

Write-Host ""
Write-Host "Setup complete!" -ForegroundColor Green
Write-Host "  backend\.venv\Scripts\uvicorn.exe app.main:app --reload --app-dir backend"
Write-Host "  cd frontend && npm run dev"
