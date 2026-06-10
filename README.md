# 🏎️ Car Finder

A personal dashboard that scrapes used-car listings, enriches them with a **local AI model**, and surfaces genuinely good deals on sports / project / classic cars around the Bay Area — without the SUV/Prius/dealer/ad noise.

- **Sources:** Craigslist (Bay Area + driveable NorCal), Bring a Trailer, Cars & Bids, eBay Motors
- **AI:** runs fully local on your GPU via [Ollama](https://ollama.com) — no API cost, nothing leaves your machine
- **Deal score (1–10):** grounded in *real sold prices* mined from BaT/Cars&Bids/eBay, normalized to local fair value
- **Per listing:** parsed specs · private-vs-dealer detection · red flags (salvage/rebuilt/high-mileage) · model-specific known quirks · tailored questions to ask the seller
- **Dashboard:** split map (local cars) + filterable scored list (all sources)

## Setup

👉 **See [SETUP.md](SETUP.md)** — one command installs every tool, library, and AI model on macOS or Windows.

```bash
# macOS (dev)
bash scripts/setup.sh
```
```powershell
# Windows (your 5080 PC)
.\scripts\setup.ps1
```

## Build status

| Phase | Scope | Status |
|------|-------|--------|
| **0** | Project scaffold, dependencies, installer, models, DB | ✅ this commit |
| **1** | Craigslist → AI extraction → scored list UI | ⏳ next |
| **2** | BaT/C&B sold-comps backfill → real deal-rating engine | ⏳ |
| **3** | Map + auctions + eBay API + saved searches + alerts | ⏳ |
| **4** | Vision (odometer/title), sold-comps explorer, polish | ⏳ |

## Stack

Python · FastAPI · Playwright/httpx · APScheduler · PostgreSQL+PostGIS · Ollama (Qwen2.5 + Llama-Vision) · Next.js · Tailwind · MapLibre
