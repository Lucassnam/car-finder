# Car Finder — Setup & Requirements

This is the single doc for getting the whole thing running. It installs **every system tool, library, and AI model** with one command. It covers both machines:

- 🍎 **macOS** — your **dev** machine (where you write/test code)
- 🪟 **Windows** — your **5080 PC** (where it actually lives and runs 24/7)

The workflow: build on the Mac → push to git → pull on the PC → run one script.

---

## 1. What gets installed

| Layer | Tool / package | Installed by |
|------|----------------|--------------|
| Version control | Git | system installer |
| Backend runtime | Python 3.12 | system installer |
| Frontend runtime | Node.js LTS (20+) | system installer |
| Database | Docker Desktop → PostgreSQL 16 + PostGIS | system installer + `docker compose` |
| Local AI | Ollama | system installer |
| Python libs | FastAPI, Playwright, SQLAlchemy, scikit-learn, … | `backend/requirements.txt` |
| Browser engine | Chromium (for Playwright) | `playwright install` |
| Frontend libs | Next.js, React, MapLibre, Tailwind, … | `frontend/package.json` |
| **AI models** | `qwen2.5:14b`, `llama3.2-vision:11b`, `nomic-embed-text` | `scripts/pull-models.*` |

**Disk footprint:** the AI models are the big items — about **17–18 GB** total. Plus a few GB for Docker/Postgres, Python, and `node_modules`.

---

## 2. Hardware notes

**Your PC (target):** RTX **5080 (16 GB VRAM)** + 64 GB RAM is more than enough.
- `qwen2.5:14b` (~9 GB) loads fully on the GPU and runs fast — this is the workhorse.
- `llama3.2-vision:11b` (~8 GB) fits for reading odometer/title photos.
- Optional `qwen2.5:32b` (~20 GB) exceeds 16 GB VRAM, so it partially offloads into your 64 GB RAM — slower but usable when you want max reasoning quality. It's commented out in the pull script.

**Your Mac (dev):** Ollama uses Apple Metal automatically. A 14B model runs fine for development/testing on Apple Silicon with 16 GB+ unified memory; if your Mac is tight on RAM, swap `LLM_TEXT_MODEL` to `qwen2.5:7b` in `.env` for local testing — the PC keeps the 14B.

> The GPU is used by **Ollama directly** (native install). Docker only runs Postgres, so you do **not** need the NVIDIA Container Toolkit or GPU passthrough into Docker.

---

## 3. One-shot install

### 🍎 macOS (dev machine)

Prerequisite: [Homebrew](https://brew.sh) and [Docker Desktop](https://www.docker.com/products/docker-desktop/) (the script installs Docker via Homebrew, but you must **open Docker Desktop once** so the engine is running).

```bash
cd "car-finder"
bash scripts/setup.sh
```

### 🪟 Windows (your 5080 PC)

Prerequisite: Windows 10/11 with `winget` (built into Win 11) and an up-to-date **NVIDIA GeForce driver** (so Ollama sees the 5080). Open PowerShell **as your normal user** in the project folder:

```powershell
cd car-finder
# If scripts are blocked the first time:
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\setup.ps1
```

> If a tool was *freshly* installed, close & reopen PowerShell (so `PATH` refreshes) and run the script again — it's safe to re-run. Also **launch Docker Desktop once** before/while it runs.

The script does, in order: install system tools → create `backend/.venv` and install Python libs → install Chromium for Playwright → `npm install` the frontend → copy `.env.example` → `.env` → start Postgres in Docker → pull the AI models.

---

## 4. Shipping Mac → PC

Use git as the pipe between machines.

```bash
# On the Mac, once:
cd "car-finder"
git init && git add -A && git commit -m "Phase 0: scaffold + setup"
# create a private repo on GitHub, then:
git remote add origin <your-private-repo-url>
git push -u origin main
```

```powershell
# On the PC:
git clone <your-private-repo-url> car-finder
cd car-finder
.\scripts\setup.ps1
```

`.env`, `node_modules/`, the Python venv, and the Postgres data are git-ignored, so each machine builds its own — you only ship code + manifests.

---

## 5. Running it

> Phase 0 sets up the **environment**. The app code (API + dashboard) lands in Phase 1 — these commands are what you'll use once it's in.

```bash
# Database (both OSes, via Docker)
docker compose up -d db

# Backend API  — macOS:  make backend     Windows:
backend\.venv\Scripts\uvicorn.exe app.main:app --reload --app-dir backend

# Frontend dashboard
cd frontend && npm run dev      # → http://localhost:3000
```

On macOS the `Makefile` has shortcuts: `make db-up`, `make backend`, `make frontend`, `make models`.

---

## 6. Configuration (`.env`)

The installer creates `.env` from `.env.example`. Worth setting:

- **`CL_REGIONS`** — Craigslist subregions to sweep (default: `sfbay,sacramento,santacruz,monterey,stockton`).
- **`EBAY_CLIENT_ID` / `EBAY_CLIENT_SECRET`** — free keys from [developer.ebay.com](https://developer.ebay.com) for the eBay Motors source. Leave blank to skip eBay.
- **`ALERT_NTFY_TOPIC`** or **`ALERT_DISCORD_WEBHOOK`** — where deal alerts get pushed; **`ALERT_MIN_SCORE`** sets the bar (default 8).
- **`LLM_*`** — which Ollama models to use; change these to trade speed vs quality.

---

## 7. Verify the install

```bash
ollama list                         # should list qwen2.5:14b, llama3.2-vision:11b, nomic-embed-text
docker compose ps                   # carfinder-db should be "healthy"
backend/.venv/bin/python -c "import fastapi, playwright, sqlalchemy; print('backend OK')"
cd frontend && npm run build         # frontend compiles
```

Quick model smoke test:
```bash
ollama run qwen2.5:14b "Say hello in 3 words."
```

---

## 8. Troubleshooting

| Symptom | Fix |
|--------|-----|
| `ollama: command not found` after install | Reopen the terminal so `PATH` updates; re-run the script. |
| Model pull is slow | They're 8–9 GB each; first pull just takes a while. Re-running resumes. |
| `docker compose` errors | Make sure **Docker Desktop is open and running** before the DB step. |
| PowerShell "running scripts is disabled" | `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` then re-run. |
| Ollama not using the 5080 | Update the NVIDIA GeForce driver; check `ollama ps` shows GPU. |
| Port 5432 already in use | Set `POSTGRES_PORT` in `.env` to e.g. `5433`. |
| Mac runs out of memory on 14B | Set `LLM_TEXT_MODEL=qwen2.5:7b` in `.env` for dev. |
