"""
Step 1 of AI enrichment: extract structured fields from raw listing text.
The Pydantic schema is passed as JSON schema to Ollama → guaranteed valid output.
"""
from loguru import logger
from ..schemas.listing import ExtractionResult
from ..scrapers.base import RawListing
from .client import get_client

SYSTEM_PROMPT = """\
You are an expert at parsing used-car listings into structured data.
Extract fields accurately from the listing title and body.
For `is_enthusiast_car`, return true ONLY for sports cars, classics, muscle cars, \
JDM imports, performance cars — NOT trucks, SUVs, minivans, economy sedans, or appliance-tier cars like Prius/Camry/Accord.
For `listing_type`, look for dealer-like signals (phone numbers repeated across listings, \
"dealer license", stock photos, fleet phrasing) to identify dealers posing as private sellers.
Be conservative: if unsure, mark spam_score low and confidence lower.
Return ONLY the JSON object — no explanation, no markdown."""


def extract_listing(raw: RawListing) -> ExtractionResult:
    """
    Takes a RawListing and returns structured ExtractionResult from the LLM.
    Pre-parsed fields from the scraper (year, mileage, etc.) are passed in the
    prompt so the model can validate/correct them rather than hallucinating.
    """
    # Seed the prompt with any structurally-parsed fields for the model to anchor on
    known = []
    if raw.year:
        known.append(f"Structurally parsed year: {raw.year}")
    if raw.mileage:
        known.append(f"Structurally parsed mileage: {raw.mileage}")
    if raw.transmission:
        known.append(f"Structurally parsed transmission: {raw.transmission}")
    if raw.title_status:
        known.append(f"Structurally parsed title status: {raw.title_status}")
    if raw.vin:
        known.append(f"Structurally parsed VIN: {raw.vin}")
    if raw.price:
        known.append(f"Asking price: ${raw.price:,}")

    known_block = ("\n\nPRE-PARSED FIELDS (validate/correct these):\n" + "\n".join(known)) if known else ""

    prompt = f"""\
LISTING TITLE: {raw.title}

LISTING BODY:
{raw.raw_text[:3000]}
{known_block}

Extract the structured fields for this listing."""

    try:
        result = get_client().structured(prompt, ExtractionResult, system=SYSTEM_PROMPT)
        # Override with structurally-parsed values where we're more confident than the LLM
        if raw.year and not result.year:
            result.year = raw.year
        if raw.mileage and not result.mileage:
            result.mileage = raw.mileage
        if raw.price and not result.price:
            result.price = raw.price
        return result
    except Exception as e:
        logger.error(f"Extraction failed for {raw.source_id}: {e}")
        # Return a minimal result so the pipeline can continue
        return ExtractionResult(
            year=raw.year,
            mileage=raw.mileage,
            price=raw.price,
            transmission=raw.transmission,
            title_status=raw.title_status,
            vin=raw.vin,
            confidence=0.0,
        )
