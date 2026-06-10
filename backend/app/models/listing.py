import uuid
from datetime import datetime, date
from typing import Optional
from sqlalchemy import (
    String, Integer, Float, Boolean, Text, DateTime, Date,
    func, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from geoalchemy2 import Geometry
from ..db import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class Listing(Base):
    __tablename__ = "listings"
    __table_args__ = (
        UniqueConstraint("source", "source_id", name="uq_listing_source_id"),
        Index("ix_listing_make_model", "make", "model"),
        Index("ix_listing_price", "price"),
        Index("ix_listing_deal_rating", "deal_rating"),
        Index("ix_listing_scraped_at", "scraped_at"),
        Index("ix_listing_location", "location", postgresql_using="gist"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    source_id: Mapped[str] = mapped_column(String(64), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[Optional[str]] = mapped_column(Text)
    raw_text: Mapped[Optional[str]] = mapped_column(Text)

    # ── Extracted car fields ──────────────────────────────────────────────────
    year: Mapped[Optional[int]] = mapped_column(Integer)
    make: Mapped[Optional[str]] = mapped_column(String(64))
    model: Mapped[Optional[str]] = mapped_column(String(64))
    generation: Mapped[Optional[str]] = mapped_column(String(32))  # NB, E36, 996, etc.
    trim: Mapped[Optional[str]] = mapped_column(String(64))
    mileage: Mapped[Optional[int]] = mapped_column(Integer)
    price: Mapped[Optional[int]] = mapped_column(Integer)
    title_status: Mapped[Optional[str]] = mapped_column(String(32))  # clean, salvage, rebuilt
    transmission: Mapped[Optional[str]] = mapped_column(String(16))  # manual, automatic
    drivetrain: Mapped[Optional[str]] = mapped_column(String(8))    # RWD, AWD, FWD
    vin: Mapped[Optional[str]] = mapped_column(String(17))
    car_category: Mapped[Optional[str]] = mapped_column(String(32))  # sports_coupe, roadster, etc.
    is_enthusiast_car: Mapped[Optional[bool]] = mapped_column(Boolean)
    modifications: Mapped[Optional[list]] = mapped_column(JSONB, default=list)

    # ── Location ──────────────────────────────────────────────────────────────
    city: Mapped[Optional[str]] = mapped_column(String(128))
    state: Mapped[Optional[str]] = mapped_column(String(32))
    lat: Mapped[Optional[float]] = mapped_column(Float)
    lng: Mapped[Optional[float]] = mapped_column(Float)
    location: Mapped[Optional[object]] = mapped_column(Geometry("POINT", srid=4326), nullable=True)

    # ── Photos ────────────────────────────────────────────────────────────────
    photos: Mapped[Optional[list]] = mapped_column(JSONB, default=list)  # list of URLs

    # ── Listing metadata ──────────────────────────────────────────────────────
    listing_type: Mapped[Optional[str]] = mapped_column(String(16))  # private, dealer
    is_dealer: Mapped[bool] = mapped_column(Boolean, default=False)
    is_spam: Mapped[bool] = mapped_column(Boolean, default=False)
    spam_score: Mapped[Optional[float]] = mapped_column(Float)  # 0–1
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    posted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # ── AI enrichment ─────────────────────────────────────────────────────────
    deal_rating: Mapped[Optional[int]] = mapped_column(Integer)  # 1–10
    deal_rationale: Mapped[Optional[str]] = mapped_column(Text)
    deal_confidence: Mapped[Optional[str]] = mapped_column(String(16))  # low, medium, high
    fair_value_estimate: Mapped[Optional[int]] = mapped_column(Integer)
    fair_value_delta: Mapped[Optional[int]] = mapped_column(Integer)  # asking minus fair (negative = deal)
    comp_count: Mapped[int] = mapped_column(Integer, default=0)
    red_flags: Mapped[Optional[list]] = mapped_column(JSONB, default=list)
    known_quirks: Mapped[Optional[list]] = mapped_column(JSONB, default=list)
    questions_to_ask: Mapped[Optional[list]] = mapped_column(JSONB, default=list)
    enriched_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # ── Dedup ─────────────────────────────────────────────────────────────────
    dedup_hash: Mapped[Optional[str]] = mapped_column(String(64), index=True)

    # ── Timestamps ────────────────────────────────────────────────────────────
    scraped_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Comp(Base):
    """Sold-price comps from BaT, Cars & Bids, eBay — Phase 2 data."""
    __tablename__ = "comps"
    __table_args__ = (
        UniqueConstraint("source", "source_id", name="uq_comp_source_id"),
        Index("ix_comp_make_model_year", "make", "model", "year"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    source_id: Mapped[str] = mapped_column(String(64), nullable=False)
    url: Mapped[Optional[str]] = mapped_column(Text)

    year: Mapped[int] = mapped_column(Integer, nullable=False)
    make: Mapped[str] = mapped_column(String(64), nullable=False)
    model: Mapped[str] = mapped_column(String(64), nullable=False)
    generation: Mapped[Optional[str]] = mapped_column(String(32))
    trim: Mapped[Optional[str]] = mapped_column(String(64))
    mileage: Mapped[Optional[int]] = mapped_column(Integer)
    sale_price: Mapped[int] = mapped_column(Integer, nullable=False)
    sale_date: Mapped[Optional[date]] = mapped_column(Date)
    transmission: Mapped[Optional[str]] = mapped_column(String(16))
    title_status: Mapped[Optional[str]] = mapped_column(String(32))
    condition_notes: Mapped[Optional[str]] = mapped_column(Text)
    modifications: Mapped[Optional[list]] = mapped_column(JSONB, default=list)
    raw_data: Mapped[Optional[dict]] = mapped_column(JSONB)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class ScrapingJob(Base):
    __tablename__ = "scraping_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="running")  # running, completed, failed
    listings_found: Mapped[int] = mapped_column(Integer, default=0)
    listings_new: Mapped[int] = mapped_column(Integer, default=0)
    listings_enriched: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    error: Mapped[Optional[str]] = mapped_column(Text)
