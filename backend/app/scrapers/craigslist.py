"""
Craigslist cars-by-owner scraper.

Strategy:
  Full sweep  — paginate the HTML search results every ~3 h, collect new listing IDs.
  Incremental — poll the RSS feed every ~20 min to catch new postings cheaply.

Politeness rules (non-negotiable per CLAUDE.md):
  - Random delay between requests (CL_MIN_DELAY / CL_MAX_DELAY from settings)
  - Only fetch detail pages for listing IDs not already in the DB
  - Exponential back-off on 403/429
  - Realistic headers
"""
import asyncio
import re
import random
from datetime import datetime, timezone
from typing import AsyncIterator, Optional, List
from urllib.parse import urlencode

import httpx
import feedparser
from selectolax.parser import HTMLParser
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from .base import BaseScraper, RawListing
from ..config import settings

# Craigslist region → hostname
def _cl_host(region: str) -> str:
    return f"https://{region}.craigslist.org"

SEARCH_PATH = "/search/cto"   # cars+trucks by owner
RSS_PATH    = "/search/cto"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# Craigslist returns 120 results per page
PAGE_SIZE = 120


class CraigslistScraper(BaseScraper):
    source_name = "craigslist"

    def __init__(self, regions: Optional[List[str]] = None):
        self.regions = regions or settings.cl_region_list

    # ─── Public interface ──────────────────────────────────────────────────

    async def scrape(self) -> AsyncIterator[RawListing]:
        """Full sweep across all regions. Yields one RawListing per new detail page."""
        async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True, timeout=20) as client:
            for region in self.regions:
                logger.info(f"CL full sweep: {region}")
                async for listing in self._sweep_region(client, region):
                    yield listing

    async def scrape_new_since(self, since: Optional[datetime] = None) -> AsyncIterator[RawListing]:
        """Cheap RSS poll — only yields listings posted after `since`."""
        async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True, timeout=20) as client:
            for region in self.regions:
                async for listing in self._poll_rss(client, region, since):
                    yield listing

    # ─── Region sweep ─────────────────────────────────────────────────────

    async def _sweep_region(self, client: httpx.AsyncClient, region: str) -> AsyncIterator[RawListing]:
        host = _cl_host(region)
        start = 0
        seen_on_page = True

        while seen_on_page:
            params = {"s": start, "hasPic": "1"}
            url = f"{host}{SEARCH_PATH}?{urlencode(params)}"
            html = await self._get_html(client, url)
            if not html:
                break

            listing_urls = _parse_search_results(html, host)
            if not listing_urls:
                break

            seen_on_page = len(listing_urls) > 0
            for listing_url, source_id in listing_urls:
                detail = await self._fetch_detail(client, listing_url, source_id, region)
                if detail:
                    yield detail
                await self._polite_delay()

            start += PAGE_SIZE

    # ─── RSS incremental poll ─────────────────────────────────────────────

    async def _poll_rss(
        self, client: httpx.AsyncClient, region: str, since: Optional[datetime]
    ) -> AsyncIterator[RawListing]:
        host = _cl_host(region)
        url = f"{host}{RSS_PATH}?format=rss&hasPic=1"
        try:
            resp = await client.get(url)
            resp.raise_for_status()
        except Exception as e:
            logger.warning(f"CL RSS fetch failed for {region}: {e}")
            return

        feed = feedparser.parse(resp.text)
        for entry in feed.entries:
            posted = _parse_rss_date(entry.get("published", ""))
            if since and posted and posted <= since:
                continue

            source_id = _extract_source_id(entry.get("link", ""))
            if not source_id:
                continue

            detail = await self._fetch_detail(
                client, entry.get("link", ""), source_id, region, posted_at=posted
            )
            if detail:
                yield detail
            await self._polite_delay()

    # ─── Detail page fetch + parse ────────────────────────────────────────

    async def _fetch_detail(
        self,
        client: httpx.AsyncClient,
        url: str,
        source_id: str,
        region: str,
        posted_at: Optional[datetime] = None,
    ) -> Optional[RawListing]:
        html = await self._get_html(client, url)
        if not html:
            return None
        return _parse_detail_page(html, url, source_id, region, posted_at)

    # ─── HTTP helper ──────────────────────────────────────────────────────

    @retry(
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=2, min=4, max=60),
        retry=retry_if_exception_type(httpx.HTTPStatusError),
        reraise=False,
    )
    async def _get_html(self, client: httpx.AsyncClient, url: str) -> Optional[str]:
        try:
            resp = await client.get(url)
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            return resp.text
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (403, 429):
                logger.warning(f"CL rate-limited ({e.response.status_code}), backing off: {url}")
                raise
            logger.warning(f"CL HTTP error {e.response.status_code}: {url}")
            return None
        except Exception as e:
            logger.warning(f"CL fetch error: {url} — {e}")
            return None

    async def _polite_delay(self):
        delay = random.uniform(settings.cl_min_delay_sec, settings.cl_max_delay_sec)
        await asyncio.sleep(delay)


# ─── HTML parsers (stateless) ─────────────────────────────────────────────────

def _parse_search_results(html: str, host: str) -> List[tuple[str, str]]:
    """Return list of (absolute_url, source_id) from a CL search results page."""
    tree = HTMLParser(html)
    results = []

    # CL search result items — the new UI uses li[data-pid], old uses .result-row
    for node in tree.css("li[data-pid], li.cl-search-result"):
        pid = node.attributes.get("data-pid", "")
        link_node = node.css_first("a.cl-app-anchor, a.result-title")
        if not link_node:
            continue
        href = link_node.attributes.get("href", "")
        if not href:
            continue
        # Make absolute
        if href.startswith("/"):
            href = host + href
        source_id = pid or _extract_source_id(href)
        if source_id:
            results.append((href, source_id))

    return results


def _parse_detail_page(
    html: str,
    url: str,
    source_id: str,
    region: str,
    posted_at: Optional[datetime] = None,
) -> Optional[RawListing]:
    tree = HTMLParser(html)

    # Title
    title_node = tree.css_first("#titletextonly, h1.postingtitle")
    title = title_node.text(strip=True) if title_node else ""

    # Price
    price = None
    price_node = tree.css_first(".price, span[data-price]")
    if price_node:
        price = _parse_price(price_node.text())

    # Body text (description)
    body_node = tree.css_first("#postingbody, section#postingbody")
    raw_text = body_node.text(strip=True) if body_node else ""

    # Location from map embed
    lat = lng = None
    map_node = tree.css_first("#map, div[data-latitude]")
    if map_node:
        lat = _safe_float(map_node.attributes.get("data-latitude"))
        lng = _safe_float(map_node.attributes.get("data-longitude"))

    # Neighbourhood / city from breadcrumb or "nearby" span
    city = None
    nearby = tree.css_first(".postinginfo .nearby, span.postingtitletext small")
    if nearby:
        city = nearby.text(strip=True).strip("() ")
    if not city:
        # Fall back to the page breadcrumb
        bc = tree.css_first("span.crumb a")
        if bc:
            city = bc.text(strip=True)

    # Posted date
    if not posted_at:
        time_node = tree.css_first("time.date")
        if time_node:
            posted_at = _parse_cl_date(time_node.attributes.get("datetime", ""))

    # Attributes (year, odometer, transmission, title, VIN, etc.)
    year = mileage = transmission = title_status = vin = drivetrain = None
    for attr_group in tree.css(".attrgroup"):
        for span in attr_group.css("span"):
            text = span.text(strip=True).lower()
            label_node = span.css_first("b")
            label = label_node.text(strip=True).lower().rstrip(":") if label_node else ""
            value_node = span.css_first("a, span.valu")
            value = value_node.text(strip=True) if value_node else text

            if label in ("year",) or re.match(r"^\d{4}$", value):
                year = _safe_int(value)
            elif label in ("odometer", "mileage") or "miles" in text:
                nums = re.findall(r"\d+", value.replace(",", ""))
                if nums:
                    mileage = int(nums[0])
            elif label == "transmission":
                transmission = "manual" if "manual" in value.lower() else "automatic"
            elif label == "title status":
                title_status = _normalize_title_status(value)
            elif label == "vin":
                candidate = re.sub(r"\s+", "", value).upper()
                if len(candidate) == 17:
                    vin = candidate
            elif label == "drive":
                drivetrain = _normalize_drivetrain(value)

    # Photos — full-resolution CL image URLs
    photos = []
    for img in tree.css("div.gallery img, img.slide"):
        src = img.attributes.get("src", "")
        if "images.craigslist.org" in src:
            # Upgrade thumbnail to full-size
            src = re.sub(r"_\d+x\d+\.jpg$", "_600x450.jpg", src)
            if src not in photos:
                photos.append(src)

    if not title and not raw_text:
        return None

    return RawListing(
        source="craigslist",
        source_id=source_id,
        url=url,
        title=title,
        raw_text=raw_text,
        price=price,
        city=city,
        state=_region_to_state(region),
        lat=lat,
        lng=lng,
        photos=photos[:20],
        posted_at=posted_at,
        year=year,
        mileage=mileage,
        transmission=transmission,
        title_status=title_status,
        vin=vin,
        drivetrain=drivetrain,
    )


# ─── Utilities ────────────────────────────────────────────────────────────────

def _extract_source_id(url: str) -> Optional[str]:
    m = re.search(r"/(\d{10,})(\.html)?", url)
    return m.group(1) if m else None


def _parse_price(text: str) -> Optional[int]:
    nums = re.findall(r"\d+", text.replace(",", ""))
    if nums:
        val = int("".join(nums[:2]))
        if 100 <= val <= 10_000_000:
            return val
    return None


def _safe_float(val) -> Optional[float]:
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _safe_int(val) -> Optional[int]:
    try:
        nums = re.findall(r"\d+", str(val).replace(",", ""))
        return int(nums[0]) if nums else None
    except Exception:
        return None


def _parse_rss_date(date_str: str) -> Optional[datetime]:
    try:
        import email.utils
        parsed = email.utils.parsedate_to_datetime(date_str)
        return parsed.astimezone(timezone.utc)
    except Exception:
        return None


def _parse_cl_date(date_str: str) -> Optional[datetime]:
    """Parse CL's ISO-ish date strings like '2024-03-15T10:30:00-0700'."""
    try:
        from datetime import timezone as tz
        return datetime.fromisoformat(date_str)
    except Exception:
        return None


def _normalize_title_status(val: str) -> str:
    val = val.lower()
    for s in ("salvage", "rebuilt", "lemon", "parts"):
        if s in val:
            return s
    return "clean" if "clean" in val else "unknown"


def _normalize_drivetrain(val: str) -> str:
    val = val.lower()
    if "rwd" in val or "rear" in val:
        return "RWD"
    if "awd" in val or "4wd" in val or "all" in val:
        return "AWD"
    if "fwd" in val or "front" in val:
        return "FWD"
    return "unknown"


def _region_to_state(region: str) -> str:
    return {
        "sfbay": "CA", "sacramento": "CA", "santacruz": "CA",
        "monterey": "CA", "stockton": "CA",
    }.get(region, "CA")
