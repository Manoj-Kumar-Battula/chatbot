import uuid
from datetime import datetime
from typing import Iterable
from urllib.parse import urlparse

from sqlalchemy import JSON, DateTime, Enum, String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, validates

from app.db.base import Base

VALID_SOURCE_TYPES = {
    "webpage",
    "pdf",
    "catalog_entry",
    "policy",
    "schedule",
    "linked_document",
    "office_page",
}
VALID_FRESHNESS = {"current", "stale", "unknown"}
VALID_AVAILABILITY = {"available", "unavailable"}
VALID_CAMPUSES = {"Hammond", "Westville", "both", "unknown"}


class OfficialSource(Base):
    __tablename__ = "official_sources"
    __table_args__ = (
        UniqueConstraint("canonical_url", name="uq_official_source_canonical_url"),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        unique=True,
        nullable=False,
    )
    canonical_url: Mapped[str] = mapped_column(String(2048), nullable=False, unique=True, index=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    source_type: Mapped[str] = mapped_column(
        Enum(*sorted(VALID_SOURCE_TYPES), name="official_source_type", native_enum=False),
        nullable=False,
    )
    campus_applicability: Mapped[list[str]] = mapped_column(
        JSON,
        default=lambda: ["unknown"],
        nullable=False,
    )
    topic_tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    current_version_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    freshness_status: Mapped[str] = mapped_column(
        Enum(*sorted(VALID_FRESHNESS), name="official_source_freshness_status", native_enum=False),
        nullable=False,
        default="unknown",
    )
    availability_status: Mapped[str] = mapped_column(
        Enum(*sorted(VALID_AVAILABILITY), name="official_source_availability_status", native_enum=False),
        nullable=False,
        default="available",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP"),
    )

    @staticmethod
    def _normalize_source_url(raw_url: str) -> str:
        if not isinstance(raw_url, str):
            raise ValueError("canonical_url must be a string.")

        value = raw_url.strip()
        if not value:
            raise ValueError("canonical_url cannot be empty.")

        parsed = urlparse(value)
        if parsed.scheme.lower() not in {"http", "https"}:
            raise ValueError("canonical_url must use http or https.")
        if not parsed.hostname:
            raise ValueError("canonical_url must include a host.")
        if parsed.username or parsed.password:
            raise ValueError("canonical_url must not include credentials.")

        host = parsed.hostname.lower()
        if host == "pnw.edu" or host.endswith(".pnw.edu"):
            try:
                port = parsed.port
            except ValueError as exc:
                raise ValueError("canonical_url contains an invalid port.") from exc
            if port not in (None, 80 if parsed.scheme.lower() == "http" else 443):
                raise ValueError("canonical_url must use its standard HTTP(S) port.")
            return value

        raise ValueError("canonical_url must resolve to an official PNW domain.")

    @staticmethod
    def _normalize_campus_values(values: Iterable[str] | None) -> list[str]:
        if values is None:
            return ["unknown"]

        normalized: list[str] = []
        for raw_value in values:
            if raw_value is None:
                continue
            value = str(raw_value).strip()
            if not value:
                continue
            lowered = value.lower()
            if lowered == "hammond":
                normalized.append("Hammond")
            elif lowered == "westville":
                normalized.append("Westville")
            elif lowered in {"both", "unknown"}:
                normalized.append(lowered if lowered == "unknown" else "both")
            else:
                raise ValueError(f"Unsupported campus applicability value: {raw_value!r}")

        if not normalized:
            return ["unknown"]

        deduplicated: list[str] = []
        seen: set[str] = set()
        for value in normalized:
            if value not in seen:
                seen.add(value)
                deduplicated.append(value)
        return deduplicated

    @staticmethod
    def _normalize_tags(values: Iterable[str] | None) -> list[str]:
        if not values:
            return []

        normalized = []
        for raw_value in values:
            if raw_value is None:
                continue
            value = str(raw_value).strip()
            if value:
                normalized.append(value)
        return normalized

    @validates("canonical_url")
    def validate_canonical_url(self, key: str, value: str) -> str:
        return self._normalize_source_url(value)

    @validates("title")
    def validate_title(self, key: str, value: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("title cannot be blank.")
        return value.strip()

    @validates("source_type")
    def validate_source_type(self, key: str, value: str) -> str:
        normalized = str(value).strip()
        if normalized not in VALID_SOURCE_TYPES:
            raise ValueError(f"source_type must be one of: {sorted(VALID_SOURCE_TYPES)}")
        return normalized

    @validates("campus_applicability")
    def validate_campus_applicability(self, key: str, value: list[str] | None) -> list[str]:
        return self._normalize_campus_values(value)

    @validates("topic_tags")
    def validate_topic_tags(self, key: str, value: list[str] | None) -> list[str]:
        return self._normalize_tags(value)

    @validates("freshness_status")
    def validate_freshness_status(self, key: str, value: str) -> str:
        normalized = str(value).strip().lower()
        if normalized not in VALID_FRESHNESS:
            raise ValueError(f"freshness_status must be one of: {sorted(VALID_FRESHNESS)}")
        return normalized

    @validates("availability_status")
    def validate_availability_status(self, key: str, value: str) -> str:
        normalized = str(value).strip().lower()
        if normalized not in VALID_AVAILABILITY:
            raise ValueError(f"availability_status must be one of: {sorted(VALID_AVAILABILITY)}")
        return normalized

    def __repr__(self) -> str:
        return (
            f"OfficialSource(id={self.id!r}, canonical_url={self.canonical_url!r}, "
            f"source_type={self.source_type!r}, freshness_status={self.freshness_status!r})"
        )
