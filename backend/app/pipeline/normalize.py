"""
Normalization, deduplication, and DB upsert.

Dedup order of preference:
  1. VIN match (most reliable)
  2. (source, source_id) unique constraint
  3. Perceptual-hash + (make, model, year, mileage-bucket, price) fingerprint

Canonicalization:
  Makes / models are stored as-provided by the LLM extraction. We normalize
  capitalisation (Title Case) but don't force a rigid taxonomy in Phase 1 —
  that can be tightened once the data shape is understood.
"""
import hashlib
import re
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from loguru import logger

from ..models.listing import Listing
from ..scrapers.base import RawListing
from ..schemas.listing import ExtractionResult, EnrichmentResult
from ..ai.extract import extract_listing
from ..ai.enrich import enrich_listing


def normalize_and_upsert(raw: RawListing, db: Session) -> tuple[Listing, bool]:
    """
    Given a RawListing:
    1. Check if already in DB (by source_id or VIN).
    2. If new → run AI extraction + enrichment, persist.
    3. Return (listing, is_new).
    """
    # ── Check by source + source_id first (cheapest) ─────────────────────
    existing = db.execute(
        select(Listing).where(
            Listing.source == raw.source,
            Listing.source_id == raw.source_id,
        )
    ).scalar_one_or_none()

    if existing:
        return existing, False

    # ── AI extraction ─────────────────────────────────────────────────────
    logger.info(f"New listing {raw.source}/{raw.source_id} — extracting…")
    extraction: ExtractionResult = extract_listing(raw)

    # ── VIN dedup (catches reposts) ───────────────────────────────────────
    if extraction.vin:
        vin_match = db.execute(
            select(Listing).where(Listing.vin == extraction.vin)
        ).scalar_one_or_none()
        if vin_match:
            logger.info(f"Dedup by VIN {extraction.vin} → existing {vin_match.id}")
            return vin_match, False

    # ── AI enrichment ─────────────────────────────────────────────────────
    enrichment: EnrichmentResult = enrich_listing(extraction, raw.raw_text, extraction.price or raw.price)

    # ── Build dedup hash for perceptual fingerprinting ───────────────────
    dedup_hash = _make_dedup_hash(extraction, raw)

    # ── Hash dedup check ─────────────────────────────────────────────────
    if dedup_hash:
        hash_match = db.execute(
            select(Listing).where(Listing.dedup_hash == dedup_hash)
        ).scalar_one_or_none()
        if hash_match:
            logger.info(f"Dedup by hash → existing {hash_match.id}")
            return hash_match, False

    # ── Build location geometry ───────────────────────────────────────────
    location_wkt = None
    lat = raw.lat
    lng = raw.lng
    if lat and lng:
        location_wkt = f"SRID=4326;POINT({lng} {lat})"

    # ── Determine is_dealer / is_spam ─────────────────────────────────────
    is_dealer = extraction.listing_type == "dealer"
    is_spam = extraction.spam_score >= 0.7

    # ── Fair value delta ──────────────────────────────────────────────────
    price = extraction.price or raw.price
    fair_delta = None
    if price and enrichment.fair_value_estimate:
        fair_delta = price - enrichment.fair_value_estimate  # negative = good deal

    # ── Persist ───────────────────────────────────────────────────────────
    listing = Listing(
        source=raw.source,
        source_id=raw.source_id,
        url=raw.url,
        title=raw.title,
        raw_text=raw.raw_text,
        year=extraction.year or raw.year,
        make=_title_case(extraction.make),
        model=_title_case(extraction.model),
        generation=extraction.generation,
        trim=extraction.trim,
        mileage=extraction.mileage or raw.mileage,
        price=price,
        title_status=extraction.title_status or raw.title_status,
        transmission=extraction.transmission or raw.transmission,
        drivetrain=extraction.drivetrain or raw.drivetrain,
        vin=extraction.vin or raw.vin,
        car_category=extraction.car_category,
        is_enthusiast_car=extraction.is_enthusiast_car,
        modifications=extraction.modifications,
        city=raw.city,
        state=raw.state,
        lat=lat,
        lng=lng,
        location=location_wkt,
        photos=raw.photos,
        listing_type=extraction.listing_type,
        is_dealer=is_dealer,
        is_spam=is_spam,
        spam_score=extraction.spam_score,
        posted_at=raw.posted_at,
        deal_rating=enrichment.deal_rating,
        deal_rationale=enrichment.deal_rationale,
        deal_confidence=enrichment.deal_confidence,
        fair_value_estimate=enrichment.fair_value_estimate,
        fair_value_delta=fair_delta,
        comp_count=0,
        red_flags=enrichment.red_flags,
        known_quirks=enrichment.known_quirks,
        questions_to_ask=enrichment.questions_to_ask,
        dedup_hash=dedup_hash,
    )

    db.add(listing)
    db.commit()
    db.refresh(listing)
    logger.info(
        f"Saved {listing.year} {listing.make} {listing.model} "
        f"${listing.price:,} score={listing.deal_rating} id={listing.id}"
    )
    return listing, True


def _make_dedup_hash(extraction: ExtractionResult, raw: RawListing) -> Optional[str]:
    """Fingerprint for cross-post dedup when VIN is absent."""
    make = (extraction.make or "").lower().strip()
    model = (extraction.model or "").lower().strip()
    year = str(extraction.year or raw.year or "")
    price = str(extraction.price or raw.price or "")
    # Bucket mileage to nearest 5k to tolerate minor differences between reposts
    mileage_bucket = _bucket(extraction.mileage or raw.mileage, 5000)
    city = (raw.city or "").lower().strip()

    key = f"{make}|{model}|{year}|{price}|{mileage_bucket}|{city}"
    if not any([make, model, year]):
        return None
    return hashlib.sha256(key.encode()).hexdigest()[:32]


def _bucket(val: Optional[int], size: int) -> str:
    if val is None:
        return ""
    return str((val // size) * size)


def _title_case(s: Optional[str]) -> Optional[str]:
    if not s:
        return s
    return re.sub(r"\b\w", lambda m: m.group().upper(), s.strip())
