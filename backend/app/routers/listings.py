from math import ceil
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_, or_
from sqlalchemy.sql.expression import desc, asc

from ..db import get_db
from ..models.listing import Listing
from ..schemas.listing import ListingOut, ListingDetail, PaginatedListings

router = APIRouter(prefix="/listings", tags=["listings"])


@router.get("", response_model=PaginatedListings)
def list_listings(
    db: Session = Depends(get_db),
    make: Optional[str] = Query(None),
    model: Optional[str] = Query(None),
    min_year: Optional[int] = Query(None),
    max_year: Optional[int] = Query(None),
    min_price: Optional[int] = Query(None),
    max_price: Optional[int] = Query(None),
    min_score: Optional[int] = Query(None, ge=1, le=10),
    transmission: Optional[str] = Query(None),
    title_status: Optional[str] = Query(None),
    private_only: bool = Query(True),
    enthusiast_only: bool = Query(True),
    source: Optional[str] = Query(None),
    sort_by: str = Query("deal_rating"),
    sort_dir: str = Query("desc"),
    page: int = Query(1, ge=1),
    per_page: int = Query(40, ge=1, le=120),
):
    q = select(Listing).where(
        Listing.is_active == True,
        Listing.is_spam == False,
    )

    if make:
        q = q.where(Listing.make.ilike(f"%{make}%"))
    if model:
        q = q.where(Listing.model.ilike(f"%{model}%"))
    if min_year:
        q = q.where(Listing.year >= min_year)
    if max_year:
        q = q.where(Listing.year <= max_year)
    if min_price:
        q = q.where(Listing.price >= min_price)
    if max_price:
        q = q.where(Listing.price <= max_price)
    if min_score:
        q = q.where(Listing.deal_rating >= min_score)
    if transmission:
        q = q.where(Listing.transmission == transmission)
    if title_status:
        q = q.where(Listing.title_status == title_status)
    if private_only:
        q = q.where(Listing.is_dealer == False)
    if enthusiast_only:
        q = q.where(Listing.is_enthusiast_car == True)
    if source:
        q = q.where(Listing.source == source)

    # Total count for pagination
    count_q = select(func.count()).select_from(q.subquery())
    total = db.execute(count_q).scalar_one()

    # Sort
    sort_col = {
        "deal_rating": Listing.deal_rating,
        "price": Listing.price,
        "posted_at": Listing.posted_at,
        "mileage": Listing.mileage,
        "scraped_at": Listing.scraped_at,
    }.get(sort_by, Listing.deal_rating)

    order_fn = desc if sort_dir == "desc" else asc
    q = q.order_by(order_fn(sort_col).nulls_last())

    # Paginate
    offset = (page - 1) * per_page
    q = q.offset(offset).limit(per_page)

    items = db.execute(q).scalars().all()

    return PaginatedListings(
        total=total,
        page=page,
        per_page=per_page,
        pages=ceil(total / per_page) if total else 0,
        items=[ListingOut.model_validate(item) for item in items],
    )


@router.get("/{listing_id}", response_model=ListingDetail)
def get_listing(listing_id: str, db: Session = Depends(get_db)):
    listing = db.get(Listing, listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return ListingDetail.model_validate(listing)


@router.get("/map/points", response_model=list[dict])
def map_points(
    db: Session = Depends(get_db),
    private_only: bool = Query(True),
    enthusiast_only: bool = Query(True),
    min_score: Optional[int] = Query(None),
    min_price: Optional[int] = Query(None),
    max_price: Optional[int] = Query(None),
    make: Optional[str] = Query(None),
):
    """Lightweight endpoint for map pins — only returns id, lat, lng, score, make, model, price."""
    q = select(
        Listing.id, Listing.lat, Listing.lng,
        Listing.deal_rating, Listing.make, Listing.model,
        Listing.year, Listing.price, Listing.title_status,
    ).where(
        Listing.is_active == True,
        Listing.is_spam == False,
        Listing.lat != None,
        Listing.lng != None,
    )

    if private_only:
        q = q.where(Listing.is_dealer == False)
    if enthusiast_only:
        q = q.where(Listing.is_enthusiast_car == True)
    if min_score:
        q = q.where(Listing.deal_rating >= min_score)
    if min_price:
        q = q.where(Listing.price >= min_price)
    if max_price:
        q = q.where(Listing.price <= max_price)
    if make:
        q = q.where(Listing.make.ilike(f"%{make}%"))

    rows = db.execute(q).all()
    return [
        {
            "id": r.id, "lat": r.lat, "lng": r.lng,
            "score": r.deal_rating, "make": r.make, "model": r.model,
            "year": r.year, "price": r.price, "title_status": r.title_status,
        }
        for r in rows
    ]
