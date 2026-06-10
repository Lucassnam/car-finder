# CLAUDE.md — Car Finder

Project guide for any Claude session working on this repo. Read this first; it captures decisions that are **not** yet visible in code.

---

## 1. What this is (and why)

A **personal** dashboard that scrapes used-car listings, enriches each one with a **local AI model**, and surfaces genuinely good deals on **sports / project / classic cars** around the Bay Area. The owner buys used enthusiast cars with his dad and finds Craigslist et al. too noisy (SUVs, Priuses, ads, dealers). This tool cuts that noise and adds: a 1–10 deal score, red flags, model-specific quirks, and questions to ask the seller.

**It is personal-use only.** Polite/rate-limited scraping, no republishing, no commercial use. Keep that posture in every scraping decision.

---

## 2. Current status

- **Phase 0 (done):** project scaffold, dependency manifests, one-shot installers, AI models, Postgres+PostGIS via Docker. See `SETUP.md`.
- **Phase 1 (done):** Full backend + frontend. Craigslist scraper, AI extract/enrich pipeline, Postgres+PostGIS, FastAPI API, Next.js split map+list dashboard. All code is in place; the app is runnable. See §9 to start it.
- **Phase 2 (next):** BaT + C&B + eBay sold-data backfill → real comps DB → replace LLM-estimate deal scores with real valuation model.

When you build Phase 2, update this file's status and the roadmap.

---

## 3. Locked design decisions (do not silently change these)

| Decision | Choice | Notes |
|---|---|---|
| **Hosting** | Owner's always-on Windows PC (RTX 5080, 64 GB RAM) | Residential IP = key to not getting blocked. Dev happens on a Mac, ships via git. |
| **AI** | **Fully local via Ollama** — no paid cloud LLM | `qwen2.5:14b` (text/reasoning), `llama3.2-vision:11b` (photos), `nomic-embed-text` (dedup/search). Don't add a cloud LLM dependency without asking. |
| **Sources** | Craigslist (core), Bring a Trailer, Cars & Bids, eBay Motors | **Facebook Marketplace deliberately excluded** (login/anti-bot/ToS). |
| **eBay access** | Official **eBay Browse API**, NOT HTML scraping | Free dev keys in `.env` (`EBAY_CLIENT_ID/SECRET`). |
| **Geography** | Craigslist = SF Bay + driveable NorCal (`CL_REGIONS` in `.env`); auctions = national (they ship) | |
| **Deal score** | Grounded in **real sold prices** mined from BaT/C&B/eBay into a comps DB | See §6. LLM estimate is only a cold-start fallback. |
| **Layout** | Split: map (located/local cars) left + filterable scored list right; auctions in their own tab | |
| **Hunting focus** | "Affordable project & fun" — Miata, E36/E46, 350Z/370Z, S2000, GTI | Budget is a **filter** (no hard cap, default ~<$30k). |
| **Dealer filter** | Private-party preferred as a **default-on toggle**, not a permanent hide | |

---

## 4. Architecture

```
 SCRAPERS              NORMALIZE          AI ENRICH (local GPU)        STORE            DASHBOARD
 Craigslist/BaT/  ──▶  unified schema ──▶ extract specs · flags ·  ──▶ Postgres   ──▶  map + scored
 C&B/eBay(API)         + dedupe (VIN/      deal score · quirks ·       +PostGIS         list, filters,
 (scheduled)           perceptual hash)    seller questions            + comps DB       alerts
```

Two data flows feed one DB:
1. **Live listings** — what's for sale now (all sources).
2. **Sold comps** — actual final prices mined from BaT/C&B/eBay results; powers the deal score (§6).

---

## 5. Tech stack & layout

**Backend** — Python 3.12, FastAPI, Playwright + httpx/selectolax (scraping), APScheduler (jobs), SQLAlchemy 2.0 + Alembic (migrations), GeoAlchemy2 (PostGIS), `ollama` client, scikit-learn/pandas (valuation), ImageHash (dedup).

**Frontend** — Next.js 15 (App Router) + React 19 + TypeScript, Tailwind + shadcn/ui, MapLibre GL (free OSM tiles, no token), TanStack Query, Recharts (comps chart).

**Data** — PostgreSQL 16 + PostGIS in Docker (`docker-compose.yml`).

**Proposed Phase-1 backend structure** (create as you go):
```
backend/app/
  main.py            # FastAPI app
  config.py          # pydantic-settings, reads .env
  db.py              # engine/session
  models/            # SQLAlchemy models (Listing, Comp, SavedSearch, ...)
  schemas/           # Pydantic — DOUBLES AS the LLM extraction contract
  scrapers/
    base.py          # common adapter interface
    craigslist.py
    bringatrailer.py
    carsandbids.py
    ebay.py          # uses Browse API
  ai/
    client.py        # Ollama wrapper, JSON-constrained calls
    extract.py       # listing → structured fields
    enrich.py        # deal score, flags, quirks, questions
    vision.py        # odometer/title photo reads
  pipeline/
    normalize.py     # canonical make/model, dedupe
    schedule.py      # APScheduler jobs
  valuation/         # sold-comps model
  alerts.py
```

---

## 6. Deal-rating engine (the hard part — get this right)

- **Ground truth = real sold prices** from BaT + C&B (+ eBay completed). Store each as a comp keyed by make/model/generation/year/mileage/transmission/mods/condition/sale_date/source.
- **Valuation:** predict fair value for a target car from its comps. Start simple — recency-weighted median/regression on (year, mileage) within model+generation — then graduate to a small gradient-boosted model per model-family as data grows.
- **Score:** `deal_rating` ∈ 1–10 from where asking price sits vs predicted value. **Always surface the $ delta, the comp count, and a confidence level** ("based on 14 sold E46 M3 6-spd, last 12 mo").
- **Curation-premium adjustment:** BaT/C&B cars are curated/national and carry an auction premium. Discount it so a Craigslist car is scored against realistic *local* value, not an inflated one.
- **Cold start:** before comps exist for a model, fall back to the LLM's market estimate, **clearly flagged low-confidence**. A one-time historical backfill of BaT/C&B sold results for the target models seeds day-one scores.
- **Caveat for our lane:** affordable project cars are *under-represented* on BaT/C&B. For those, lean more on Craigslist asking-price distributions + eBay, and be honest about thin data.

---

## 7. AI enrichment jobs (per new listing, all local)

1. **Extract** → strict JSON matching a Pydantic schema: year, make, model, generation/chassis, trim, mileage, price, title_status, transmission, drivetrain, vin, location, `listing_type` (private/dealer), modifications[], spam_score.
2. **Dealer detection** → phone reuse, "dealer/license #" text, stock photos, fleet patterns → powers the private-only filter.
3. **Reason** → deal_rating + rationale, red_flags[] (salvage/rebuilt/branded/flood title, high mileage for model, scam signals), known_quirks[] (model-specific), questions_to_ask[].
4. **Vision (optional)** → read odometer photo (cross-check mileage), detect title/salvage docs, flag visible damage.

**Rules:** call Ollama with JSON-constrained output (the Pydantic schema is the contract). Re-running enrichment on the whole DB is free (local) — design prompts so a full re-score is cheap and idempotent.

---

## 8. Scraping rules (non-negotiable)

- **Be polite:** randomized delays (`CL_MIN_DELAY_SEC`/`CL_MAX_DELAY_SEC`), conservative rate, realistic headers, exponential backoff on 403/429 (use `tenacity`).
- **Cache hard:** only fetch detail pages for *new* listing IDs. Use RSS for cheap "new since last poll" on Craigslist.
- **Per-source adapters** behind one interface (`scrapers/base.py`); each normalizes into the unified `Listing` schema.
- **Dedup** by VIN if present, else hash(make, model, year, mileage-bucket, price, location, perceptual-hash of first image).
- **eBay = API, never scrape.** BaT/C&B have JSON behind their frontends; prefer that over brittle HTML.
- Playwright is the **fallback** for JS/anti-bot pages; default to httpx + selectolax for speed.

---

## 9. Dev workflow

Owner develops on **macOS**, runs production on the **Windows PC**, shipping via **git** (see `SETUP.md` §4).

```bash
# Install everything (one-shot)
bash scripts/setup.sh          # mac     |  .\scripts\setup.ps1  on Windows

# Day-to-day (mac shortcuts in Makefile)
make db-up                     # start Postgres+PostGIS
make backend                   # FastAPI (Phase 1+)
make frontend                  # Next.js dashboard (Phase 1+)
make models                    # pull/refresh Ollama models
```

- Config lives in `.env` (created from `.env.example`). **Never commit `.env` or secrets.**
- `.venv`, `node_modules`, and `pgdata` are git-ignored — each machine builds its own.
- After schema changes, create an Alembic migration (don't hand-edit the DB).

---

## 10. Roadmap

- ✅ **Phase 0** — scaffold, installers, DB, AI models.
- ✅ **Phase 1** — Craigslist scraper → AI extract+enrich → Postgres → FastAPI → Next.js split map+list. Usable end-to-end.
- **Phase 2 (next)** — BaT + C&B sold-data backfill → `backend/app/valuation/` → real comp-based deal scores replacing LLM estimate.
- **Phase 3** — Auctions tab (BaT/C&B live listings) + eBay Browse API + saved searches + ntfy/Discord alerts.
- **Phase 4** — Vision (odometer/title photo reading), sold-comps explorer UI, dedup hardening, full polish.

---

## 11. Working style for this repo

- **Don't assume — ask** when a design choice isn't covered here (the owner explicitly prefers being consulted on direction).
- Keep the local-only / no-cloud-cost and polite-scraping principles intact unless told otherwise.
- When a deal score is shown, never present it as authoritative without its confidence/comp-count.
- Update this file's **status** (§2) and **roadmap** (§10) as phases complete.
