"""Pipeline control endpoints — trigger scrapes, check job status."""
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from ..db import get_db
from ..models.listing import ScrapingJob
from ..pipeline.schedule import run_craigslist_sweep, run_craigslist_rss_poll
from ..ai.client import get_client

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


@router.post("/run/craigslist")
async def trigger_craigslist_sweep(background_tasks: BackgroundTasks):
    """Manually trigger a full Craigslist sweep (runs in background)."""
    background_tasks.add_task(run_craigslist_sweep)
    return {"status": "started", "message": "Craigslist sweep started in background"}


@router.post("/run/rss")
async def trigger_rss_poll(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_craigslist_rss_poll)
    return {"status": "started", "message": "RSS poll started in background"}


@router.get("/jobs")
def list_jobs(db: Session = Depends(get_db), limit: int = 20):
    jobs = db.execute(
        select(ScrapingJob).order_by(desc(ScrapingJob.started_at)).limit(limit)
    ).scalars().all()
    return [
        {
            "id": j.id,
            "source": j.source,
            "status": j.status,
            "listings_found": j.listings_found,
            "listings_new": j.listings_new,
            "started_at": j.started_at,
            "finished_at": j.finished_at,
            "error": j.error,
        }
        for j in jobs
    ]


@router.get("/health")
def health():
    """Check Ollama connectivity."""
    client = get_client()
    return {
        "ollama": "ok" if client.is_available() else "unavailable",
    }
