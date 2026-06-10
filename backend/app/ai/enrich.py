"""
Step 2 of AI enrichment: deal rating, red flags, model-specific quirks, seller questions.
Runs after extraction. In Phase 1, the deal score is an AI estimate (low confidence).
Phase 2 replaces it with real comp-based scoring from the valuation module.
"""
from loguru import logger
from ..schemas.listing import ExtractionResult, EnrichmentResult
from .client import get_client

SYSTEM_PROMPT = """\
You are a seasoned used-car buyer with deep knowledge of enthusiast, sports, and classic cars.
Your job: given a parsed listing, produce an honest deal assessment.

DEAL RATING SCALE (1–10, be calibrated — most listings are 4–6):
  1–2  Severely overpriced or strong scam signals
  3–4  Overpriced for condition/mileage, or significant undisclosed concerns
  5–6  Fair market price — nothing special, nothing wrong
  7–8  Noticeably below typical asking prices for this car
  9–10 Exceptional deal — well under market, rare find

In Phase 1 you have NO sold-comp data, so set deal_confidence = "low" and be honest about that.
For known_quirks, give model-specific inspection points (e.g. "Check E46 M3 subframe mounts for cracks").
For questions_to_ask, write specific questions FOR THIS LISTING given what the seller did/did not mention.
Return ONLY the JSON object."""


def enrich_listing(extraction: ExtractionResult, raw_text: str, price: int | None) -> EnrichmentResult:
    """
    Takes an ExtractionResult + original listing text and produces an EnrichmentResult.
    Called after extract_listing(); the result is merged into the DB record.
    """
    car_str = " ".join(filter(None, [
        str(extraction.year) if extraction.year else None,
        extraction.make,
        extraction.model,
        f"({extraction.generation})" if extraction.generation else None,
        extraction.trim,
        extraction.transmission,
    ]))

    mods_str = (", ".join(extraction.modifications) if extraction.modifications else "none mentioned")
    price_str = f"${price:,}" if price else "not listed"

    prompt = f"""\
CAR: {car_str or "Unknown"}
ASKING PRICE: {price_str}
MILEAGE: {f"{extraction.mileage:,} miles" if extraction.mileage else "not listed"}
TITLE: {extraction.title_status or "unknown"}
TRANSMISSION: {extraction.transmission or "unknown"}
DRIVETRAIN: {extraction.drivetrain or "unknown"}
MODIFICATIONS: {mods_str}
SPAM SCORE: {extraction.spam_score:.2f}
LISTING TYPE: {extraction.listing_type or "unknown"}

LISTING TEXT (first 2000 chars):
{raw_text[:2000]}

Produce the deal assessment, quirks, and seller questions for this specific listing."""

    try:
        return get_client().structured(prompt, EnrichmentResult, system=SYSTEM_PROMPT)
    except Exception as e:
        logger.error(f"Enrichment failed: {e}")
        return EnrichmentResult(
            deal_rating=5,
            deal_rationale="AI enrichment failed — manual review needed.",
            deal_confidence="low",
            red_flags=["enrichment-failed"],
            known_quirks=[],
            questions_to_ask=[],
        )
