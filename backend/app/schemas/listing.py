"""
Pydantic schemas — three purposes:
  1. API response shapes (ListingOut, ListingDetail)
  2. API request/filter shapes (ListingFilter)
  3. LLM extraction contracts (ExtractionResult, EnrichmentResult)
     — these are passed as JSON schema to Ollama so the model fills them in.
"""
from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, Field


# ── LLM extraction contract ───────────────────────────────────────────────────

class ExtractionResult(BaseModel):
    """Structured fields the LLM extracts from a raw listing title + body."""
    year: Optional[int] = Field(None, ge=1900, le=2030)
    make: Optional[str] = Field(None, description="Brand name, e.g. Mazda, Porsche, BMW")
    model: Optional[str] = Field(None, description="Model name, e.g. Miata, 911, M3")
    generation: Optional[str] = Field(
        None,
        description="Chassis/generation code if known, e.g. NA/NB/NC/ND for Miata, E36/E46 for 3-series, 993/996/997 for 911"
    )
    trim: Optional[str] = Field(None, description="Trim level, e.g. LS, S, Turbo, GT3")
    mileage: Optional[int] = Field(None, ge=0, le=1_000_000)
    price: Optional[int] = Field(None, ge=0)
    title_status: Optional[Literal["clean", "salvage", "rebuilt", "lemon", "parts", "unknown"]] = None
    transmission: Optional[Literal["manual", "automatic", "cvt", "unknown"]] = None
    drivetrain: Optional[Literal["RWD", "AWD", "FWD", "4WD", "unknown"]] = None
    vin: Optional[str] = Field(None, min_length=17, max_length=17)
    listing_type: Optional[Literal["private", "dealer", "unknown"]] = None
    modifications: List[str] = Field(default_factory=list, description="List of notable mods/upgrades mentioned")
    spam_score: float = Field(
        0.0, ge=0.0, le=1.0,
        description="0=legit private listing, 1=obvious spam/ad/dealer-disguised"
    )
    is_enthusiast_car: bool = Field(
        False,
        description="True if this is a sports car, classic, muscle, or enthusiast vehicle — NOT a truck, SUV, minivan, economy sedan, or daily-driver appliance"
    )
    car_category: Optional[Literal[
        "sports_coupe", "roadster_convertible", "sport_sedan",
        "muscle", "classic", "jdm_import", "track_car",
        "daily_driver", "truck_suv", "van_minivan", "unknown"
    ]] = None
    confidence: float = Field(
        1.0, ge=0.0, le=1.0,
        description="Overall confidence in extraction accuracy"
    )


class EnrichmentResult(BaseModel):
    """Reasoning the LLM adds after extraction — deal rating, quirks, questions."""
    deal_rating: int = Field(
        ..., ge=1, le=10,
        description=(
            "1=severely overpriced/scam, 5=fair market price, 8=noticeably below market, "
            "10=incredible deal. Be calibrated — most listings are 4–6."
        )
    )
    deal_rationale: str = Field(
        ...,
        description="1–2 sentence explanation of the score. Mention price vs typical market, condition signals, mods, red flags."
    )
    deal_confidence: Literal["low", "medium", "high"] = Field(
        "low",
        description="low=AI estimate only (no real comps), medium=some data, high=many confirmed comps"
    )
    fair_value_estimate: Optional[int] = Field(
        None,
        description="AI's estimate of fair market value in USD for a private-party sale in the Bay Area"
    )
    red_flags: List[str] = Field(
        default_factory=list,
        description="Specific concerns: salvage/rebuilt title, suspiciously low price, flood, very high mileage for model, scam signals, missing info"
    )
    known_quirks: List[str] = Field(
        default_factory=list,
        description="Model-specific issues to inspect or ask about, e.g. 'E46 M3 — check for subframe cracks, rod bearing service history'"
    )
    questions_to_ask: List[str] = Field(
        default_factory=list,
        description="Specific questions for this seller given this listing, e.g. 'Has the timing belt been replaced?'"
    )


# ── API response shapes ───────────────────────────────────────────────────────

class ListingOut(BaseModel):
    """Compact card-view representation used in the list + map."""
    model_config = {"from_attributes": True}

    id: str
    source: str
    url: str
    title: Optional[str]
    year: Optional[int]
    make: Optional[str]
    model: Optional[str]
    generation: Optional[str]
    trim: Optional[str]
    mileage: Optional[int]
    price: Optional[int]
    title_status: Optional[str]
    transmission: Optional[str]
    listing_type: Optional[str]
    is_dealer: bool
    is_spam: bool
    car_category: Optional[str]
    photos: Optional[List[str]]
    city: Optional[str]
    state: Optional[str]
    lat: Optional[float]
    lng: Optional[float]
    deal_rating: Optional[int]
    deal_confidence: Optional[str]
    fair_value_estimate: Optional[int]
    fair_value_delta: Optional[int]
    comp_count: int
    red_flags: Optional[List[str]]
    posted_at: Optional[datetime]
    scraped_at: datetime


class ListingDetail(ListingOut):
    """Full detail view — includes the long-form enrichment fields."""
    raw_text: Optional[str]
    drivetrain: Optional[str]
    vin: Optional[str]
    modifications: Optional[List[str]]
    deal_rationale: Optional[str]
    known_quirks: Optional[List[str]]
    questions_to_ask: Optional[List[str]]
    spam_score: Optional[float]
    enriched_at: Optional[datetime]


# ── API request/filter shapes ─────────────────────────────────────────────────

class ListingFilter(BaseModel):
    make: Optional[str] = None
    model: Optional[str] = None
    min_year: Optional[int] = None
    max_year: Optional[int] = None
    min_price: Optional[int] = None
    max_price: Optional[int] = None
    min_score: Optional[int] = None
    transmission: Optional[str] = None
    title_status: Optional[str] = None
    private_only: bool = True
    enthusiast_only: bool = True
    source: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    radius_km: Optional[float] = None
    sort_by: str = "deal_rating"   # deal_rating, price, posted_at, mileage
    sort_dir: str = "desc"
    page: int = Field(1, ge=1)
    per_page: int = Field(40, ge=1, le=120)


class PaginatedListings(BaseModel):
    total: int
    page: int
    per_page: int
    pages: int
    items: List[ListingOut]
