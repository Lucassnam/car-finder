from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from .db import engine, Base
from .routers import listings as listings_router
from .routers import pipeline as pipeline_router
from .pipeline.schedule import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Car Finder API…")
    # Create all tables (Alembic handles schema in production; this is a dev safety net)
    Base.metadata.create_all(bind=engine)
    start_scheduler()
    yield
    stop_scheduler()
    logger.info("Car Finder API shut down.")


app = FastAPI(
    title="Car Finder API",
    description="Sports-car listing aggregator — Bay Area + NorCal",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(listings_router.router, prefix="/api")
app.include_router(pipeline_router.router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok"}
