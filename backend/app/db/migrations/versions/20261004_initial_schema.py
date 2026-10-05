"""Initial source and retrieval schema.

Revision ID: 20261004_initial_schema
Revises:
Create Date: 2026-10-04 19:44:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision = "20261004_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "official_sources",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("canonical_url", sa.String(length=2048), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column(
            "source_type",
            sa.Enum(
                "webpage",
                "pdf",
                "catalog_entry",
                "policy",
                "schedule",
                "linked_document",
                "office_page",
                name="official_source_type",
                create_type=False,
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("campus_applicability", sa.JSON(), nullable=False, server_default='["unknown"]'),
        sa.Column("topic_tags", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("current_version_id", sa.String(length=36), nullable=True),
        sa.Column(
            "freshness_status",
            sa.Enum(
                "current",
                "stale",
                "unknown",
                name="official_source_freshness_status",
                create_type=False,
                native_enum=False,
            ),
            nullable=False,
            server_default="unknown",
        ),
        sa.Column(
            "availability_status",
            sa.Enum(
                "available",
                "unavailable",
                name="official_source_availability_status",
                create_type=False,
                native_enum=False,
            ),
            nullable=False,
            server_default="available",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("canonical_url", name="uq_official_source_canonical_url"),
    )
    op.create_index("ix_official_sources_canonical_url", "official_sources", ["canonical_url"], unique=True)

    op.create_table(
        "official_source_versions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("source_id", sa.String(length=36), nullable=False),
        sa.Column("content_sha256", sa.String(length=128), nullable=False),
        sa.Column("document_date", sa.Date(), nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("effective_from", sa.Date(), nullable=True),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("etag", sa.String(length=255), nullable=True),
        sa.Column("last_modified", sa.String(length=255), nullable=True),
        sa.Column("parser_name", sa.String(length=255), nullable=False),
        sa.Column("parser_version", sa.String(length=64), nullable=False),
        sa.Column(
            "extraction_status",
            sa.Enum(
                "complete",
                "partial",
                "failed",
                name="official_source_version_extraction_status",
                create_type=False,
                native_enum=False,
            ),
            nullable=False,
            server_default="complete",
        ),
        sa.Column(
            "freshness_status",
            sa.Enum(
                "current",
                "stale",
                "unknown",
                "missing",
                name="official_source_version_freshness_status",
                create_type=False,
                native_enum=False,
            ),
            nullable=False,
            server_default="unknown",
        ),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("supersedes_version_id", sa.String(length=36), nullable=True),
        sa.Column("raw_object_uri", sa.String(length=2048), nullable=True),
        sa.Column("raw_content", sa.LargeBinary(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["source_id"], ["official_sources.id"], name="fk_official_source_versions_source_id_official_sources"),
        sa.UniqueConstraint("source_id", "content_sha256", name="uq_official_source_version_content"),
    )
    op.create_index("ix_official_source_versions_source_id", "official_source_versions", ["source_id"])
    op.create_index("ix_official_source_versions_content_sha256", "official_source_versions", ["content_sha256"])

    op.create_table(
        "retrieval_chunks",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("version_id", sa.String(length=36), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("heading_path", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("section_ref", sa.String(length=512), nullable=True),
        sa.Column("page_start", sa.Integer(), nullable=True),
        sa.Column("page_end", sa.Integer(), nullable=True),
        sa.Column("html_anchor", sa.String(length=512), nullable=True),
        sa.Column("link_targets", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("campus_scope", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("term_scope", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("course_code", sa.String(length=64), nullable=True),
        sa.Column("event_type", sa.String(length=128), nullable=True),
        sa.Column("table_id", sa.String(length=256), nullable=True),
        sa.Column("table_row_key", sa.String(length=256), nullable=True),
        sa.Column("table_column_headers", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("embedding_model", sa.String(length=255), nullable=True),
        sa.Column("embedding_dimensions", sa.Integer(), nullable=True),
        sa.Column("embedding", Vector(384), nullable=True),
        sa.Column("search_text", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["version_id"], ["official_source_versions.id"], name="fk_retrieval_chunks_version_id_official_source_versions"),
    )
    op.create_index("ix_retrieval_chunks_version_id", "retrieval_chunks", ["version_id"])
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_retrieval_chunks_fulltext "
        "ON retrieval_chunks USING GIN (to_tsvector('english', coalesce(search_text, '')))"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_retrieval_chunks_fulltext")
    op.drop_index(op.f("ix_retrieval_chunks_version_id"), table_name="retrieval_chunks")
    op.drop_table("retrieval_chunks")
    op.drop_index(op.f("ix_official_source_versions_content_sha256"), table_name="official_source_versions")
    op.drop_index(op.f("ix_official_source_versions_source_id"), table_name="official_source_versions")
    op.drop_table("official_source_versions")
    op.drop_index(op.f("ix_official_sources_canonical_url"), table_name="official_sources")
    op.drop_table("official_sources")
    op.execute("DROP EXTENSION IF EXISTS vector")
