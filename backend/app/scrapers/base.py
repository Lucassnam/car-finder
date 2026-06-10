"""Abstract base that all source-specific scrapers must implement."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import AsyncIterator, Optional


@dataclass
class RawListing:
    """Minimal, un-enriched listing as scraped from the source."""
    source: str
    source_id: str
    url: str
    title: str
    raw_text: str
    price: Optional[int] = None
    city: Optional[str] = None
    state: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    photos: list = field(default_factory=list)
    posted_at: Optional[datetime] = None
    # Pre-parsed fields when the source provides them structurally
    year: Optional[int] = None
    make: Optional[str] = None
    model_name: Optional[str] = None  # "model" conflicts with pydantic
    mileage: Optional[int] = None
    transmission: Optional[str] = None
    title_status: Optional[str] = None
    vin: Optional[str] = None
    drivetrain: Optional[str] = None


class BaseScraper(ABC):
    source_name: str = ""

    @abstractmethod
    async def scrape(self) -> AsyncIterator[RawListing]:
        """Yield RawListing objects one at a time, respecting rate limits."""
        ...

    @abstractmethod
    async def scrape_new_since(self, since: Optional[datetime]) -> AsyncIterator[RawListing]:
        """Yield only listings newer than `since` (used for incremental polling)."""
        ...
