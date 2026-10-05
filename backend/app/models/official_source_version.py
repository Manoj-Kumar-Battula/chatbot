import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, LargeBinary, String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.db.base import Base

VALID_EXTRACTION_STATUS = {"complete", "partial", "failed"}
VALID_FRESHNESS = {"current", "stale", "unknown", "missing"}


class OfficialSourceVersion(Base):
    __tablename__ = "official_source_versions"
    __table_args__ = (
        UniqueConstraint("source_id", "content_sha256", name="uq_official_source_version_content"),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False,
        unique=True,
    )
    source_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("official_sources.id"),
        nullable=False,
        index=True,
    )
    content_sha256: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    document_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    effective_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    etag: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_modified: Mapped[str | None] = mapped_column(String(255), nullable=True)
    parser_name: Mapped[str] = mapped_column(String(255), nullable=False)
    parser_version: Mapped[str] = mapped_column(String(64), nullable=False)
    extraction_status: Mapped[str] = mapped_column(
        Enum(*sorted(VALID_EXTRACTION_STATUS), name="official_source_version_extraction_status", native_enum=False),
        nullable=False,
        default="complete",
    )
    freshness_status: Mapped[str] = mapped_column(
        Enum(*sorted(VALID_FRESHNESS), name="official_source_version_freshness_status", native_enum=False),
        nullable=False,
        default="unknown",
    )
    is_current: Mapped[bool] = mapped_column(default=False, nullable=False)
    supersedes_version_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    raw_object_uri: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    raw_content: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    source = relationship("OfficialSource", backref="versions")
    chunks = relationship("RetrievalChunk", back_populates="version", cascade="all, delete-orphan")

    @validates("content_sha256")
    def validate_content_sha256(self, key: str, value: str) -> str:
        normalized = str(value).strip()
        if len(normalized) != 64 or any(ch not in "0123456789abcdefABCDEF" for ch in normalized):
            raise ValueError("content_sha256 must be a 64-character hexadecimal SHA256 digest.")
        return normalized.lower()

    @validates("parser_name")
    def validate_parser_name(self, key: str, value: str) -> str:
        normalized = str(value).strip()
        if not normalized:
            raise ValueError("parser_name cannot be blank.")
        return normalized

    @validates("parser_version")
    def validate_parser_version(self, key: str, value: str) -> str:
        normalized = str(value).strip()
        if not normalized:
            raise ValueError("parser_version cannot be blank.")
        return normalized

    @validates("extraction_status")
    def validate_extraction_status(self, key: str, value: str) -> str:
        normalized = str(value).strip().lower()
        if normalized not in VALID_EXTRACTION_STATUS:
            raise ValueError(f"extraction_status must be one of: {sorted(VALID_EXTRACTION_STATUS)}")
        return normalized

    @validates("freshness_status")
    def validate_freshness_status(self, key: str, value: str) -> str:
        normalized = str(value).strip().lower()
        if normalized not in VALID_FRESHNESS:
            raise ValueError(f"freshness_status must be one of: {sorted(VALID_FRESHNESS)}")
        return normalized

    def __repr__(self) -> str:
        return (
            f"OfficialSourceVersion(id={self.id!r}, source_id={self.source_id!r}, "
            f"content_sha256={self.content_sha256!r}, freshness_status={self.freshness_status!r})"
        )
