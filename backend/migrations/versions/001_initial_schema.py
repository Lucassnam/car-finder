"""Initial schema — listings, comps, scraping_jobs

Revision ID: 001
Revises:
Create Date: 2026-06-10
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import geoalchemy2

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    op.create_table(
        "listings",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("source", sa.String(32), nullable=False),
        sa.Column("source_id", sa.String(64), nullable=False),
        sa.Column("url", sa.Text, nullable=False),
        sa.Column("title", sa.Text),
        sa.Column("raw_text", sa.Text),
        # Car fields
        sa.Column("year", sa.Integer),
        sa.Column("make", sa.String(64)),
        sa.Column("model", sa.String(64)),
        sa.Column("generation", sa.String(32)),
        sa.Column("trim", sa.String(64)),
        sa.Column("mileage", sa.Integer),
        sa.Column("price", sa.Integer),
        sa.Column("title_status", sa.String(32)),
        sa.Column("transmission", sa.String(16)),
        sa.Column("drivetrain", sa.String(8)),
        sa.Column("vin", sa.String(17)),
        sa.Column("car_category", sa.String(32)),
        sa.Column("is_enthusiast_car", sa.Boolean),
        sa.Column("modifications", postgresql.JSONB),
        # Location
        sa.Column("city", sa.String(128)),
        sa.Column("state", sa.String(32)),
        sa.Column("lat", sa.Float),
        sa.Column("lng", sa.Float),
        sa.Column("location", geoalchemy2.Geometry("POINT", srid=4326), nullable=True),
        # Photos
        sa.Column("photos", postgresql.JSONB),
        # Metadata
        sa.Column("listing_type", sa.String(16)),
        sa.Column("is_dealer", sa.Boolean, default=False),
        sa.Column("is_spam", sa.Boolean, default=False),
        sa.Column("spam_score", sa.Float),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("posted_at", sa.DateTime(timezone=True)),
        # AI enrichment
        sa.Column("deal_rating", sa.Integer),
        sa.Column("deal_rationale", sa.Text),
        sa.Column("deal_confidence", sa.String(16)),
        sa.Column("fair_value_estimate", sa.Integer),
        sa.Column("fair_value_delta", sa.Integer),
        sa.Column("comp_count", sa.Integer, default=0),
        sa.Column("red_flags", postgresql.JSONB),
        sa.Column("known_quirks", postgresql.JSONB),
        sa.Column("questions_to_ask", postgresql.JSONB),
        sa.Column("enriched_at", sa.DateTime(timezone=True)),
        # Dedup
        sa.Column("dedup_hash", sa.String(64)),
        # Timestamps
        sa.Column("scraped_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("source", "source_id", name="uq_listing_source_id"),
    )

    op.create_index("ix_listing_make_model", "listings", ["make", "model"])
    op.create_index("ix_listing_price", "listings", ["price"])
    op.create_index("ix_listing_deal_rating", "listings", ["deal_rating"])
    op.create_index("ix_listing_scraped_at", "listings", ["scraped_at"])
    op.create_index("ix_listing_dedup_hash", "listings", ["dedup_hash"])
    op.create_index(
        "ix_listing_location", "listings", ["location"],
        postgresql_using="gist"
    )

    op.create_table(
        "comps",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("source", sa.String(32), nullable=False),
        sa.Column("source_id", sa.String(64), nullable=False),
        sa.Column("url", sa.Text),
        sa.Column("year", sa.Integer, nullable=False),
        sa.Column("make", sa.String(64), nullable=False),
        sa.Column("model", sa.String(64), nullable=False),
        sa.Column("generation", sa.String(32)),
        sa.Column("trim", sa.String(64)),
        sa.Column("mileage", sa.Integer),
        sa.Column("sale_price", sa.Integer, nullable=False),
        sa.Column("sale_date", sa.Date),
        sa.Column("transmission", sa.String(16)),
        sa.Column("title_status", sa.String(32)),
        sa.Column("condition_notes", sa.Text),
        sa.Column("modifications", postgresql.JSONB),
        sa.Column("raw_data", postgresql.JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("source", "source_id", name="uq_comp_source_id"),
    )
    op.create_index("ix_comp_make_model_year", "comps", ["make", "model", "year"])

    op.create_table(
        "scraping_jobs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("source", sa.String(32), nullable=False),
        sa.Column("status", sa.String(16), default="running"),
        sa.Column("listings_found", sa.Integer, default=0),
        sa.Column("listings_new", sa.Integer, default=0),
        sa.Column("listings_enriched", sa.Integer, default=0),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("error", sa.Text),
    )


def downgrade() -> None:
    op.drop_table("scraping_jobs")
    op.drop_table("comps")
    op.drop_index("ix_listing_location", table_name="listings")
    op.drop_index("ix_listing_dedup_hash", table_name="listings")
    op.drop_index("ix_listing_scraped_at", table_name="listings")
    op.drop_index("ix_listing_deal_rating", table_name="listings")
    op.drop_index("ix_listing_price", table_name="listings")
    op.drop_index("ix_listing_make_model", table_name="listings")
    op.drop_table("listings")
