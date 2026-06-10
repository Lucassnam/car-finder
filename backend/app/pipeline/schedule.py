"""
APScheduler jobs:
  full_sweep  — full Craigslist paginated sweep every 3 h
  rss_poll    — cheap RSS new-listing check every 20 min
"""
from datetime import datetime, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger
from sqlalchemy import select, func

from ..db import SessionLocal
from ..models.listing import ScrapingJob
from ..scrapers.craigslist import CraigslistScraper
from .normalize import normalize_and_upsert


scheduler = AsyncIOScheduler()


async def run_craigslist_sweep():
    """Full paginated sweep across all configured CL regions."""
    db = SessionLocal()
    job = ScrapingJob(source="craigslist", status="running")
    db.add(job)
    db.commit()

    scraper = CraigslistScraper()
    found = new = 0

    try:
        async for raw in scraper.scrape():
            found += 1
            _, is_new = normalize_and_upsert(raw, db)
            if is_new:
                new += 1

        job.status = "completed"
        job.listings_found = found
        job.listings_new = new
        job.finished_at = datetime.now(timezone.utc)
        logger.info(f"CL sweep done: {found} found, {new} new")
    except Exception as e:
        logger.error(f"CL sweep failed: {e}")
        job.status = "failed"
        job.error = str(e)
        job.finished_at = datetime.now(timezone.utc)
    finally:
        db.commit()
        db.close()


async def run_craigslist_rss_poll():
    """Fast RSS poll for new listings since the last full sweep."""
    db = SessionLocal()

    # Find the most recent listing we have from CL to use as our "since" cursor
    latest_row = db.execute(
        select(func.max(ScrapingJob.finished_at)).where(
            ScrapingJob.source == "craigslist",
            ScrapingJob.status == "completed",
        )
    ).scalar_one_or_none()

    since = latest_row  # None on first run → fetch everything in RSS window

    scraper = CraigslistScraper()
    new = 0

    try:
        async for raw in scraper.scrape_new_since(since):
            _, is_new = normalize_and_upsert(raw, db)
            if is_new:
                new += 1
        if new:
            logger.info(f"RSS poll: {new} new listings")
    except Exception as e:
        logger.error(f"RSS poll failed: {e}")
    finally:
        db.close()


def start_scheduler():
    scheduler.add_job(
        run_craigslist_sweep,
        trigger=IntervalTrigger(hours=3),
        id="cl_full_sweep",
        replace_existing=True,
        next_run_time=datetime.now(timezone.utc),  # run immediately on startup
    )
    scheduler.add_job(
        run_craigslist_rss_poll,
        trigger=IntervalTrigger(minutes=20),
        id="cl_rss_poll",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started: CL sweep every 3h, RSS poll every 20min")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
