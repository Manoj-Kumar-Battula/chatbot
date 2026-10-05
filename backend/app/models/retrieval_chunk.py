import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.db.base import Base

EMBEDDING_DIMENSIONS = 384


class RetrievalChunk(Base):
    __tablename__ = "retrieval_chunks"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False,
        unique=True,
    )
    version_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("official_source_versions.id"),
        nullable=False,
        index=True,
    )
    ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    heading_path: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    section_ref: Mapped[str | None] = mapped_column(String(512), nullable=True)
    page_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    page_end: Mapped[int | None] = mapped_column(Integer, nullable=True)
    html_anchor: Mapped[str | None] = mapped_column(String(512), nullable=True)
    link_targets: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    campus_scope: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    term_scope: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    course_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    event_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    table_id: Mapped[str | None] = mapped_column(String(256), nullable=True)
    table_row_key: Mapped[str | None] = mapped_column(String(256), nullable=True)
    table_column_headers: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    embedding_model: Mapped[str | None] = mapped_column(String(255), nullable=True)
    embedding_dimensions: Mapped[int | None] = mapped_column(Integer, nullable=True)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIMENSIONS), nullable=True)
    search_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    version = relationship("OfficialSourceVersion", back_populates="chunks")

    @validates("text")
    def validate_text(self, key: str, value: str) -> str:
        normalized = str(value).strip()
        if not normalized:
            raise ValueError("text cannot be blank.")
        return normalized

    @validates("heading_path")
    def validate_heading_path(self, key: str, value: list[str] | None) -> list[str]:
        if value is None:
            return []
        return [str(item).strip() for item in value if str(item).strip()]

    @validates("link_targets")
    def validate_link_targets(self, key: str, value: list[str] | None) -> list[str]:
        if value is None:
            return []
        return [str(item).strip() for item in value if str(item).strip()]

    @validates("campus_scope")
    def validate_campus_scope(self, key: str, value: list[str] | None) -> list[str]:
        if value is None:
            return []
        clean: list[str] = []
        for item in value:
            normalized = str(item).strip()
            if normalized:
                clean.append(normalized)
        return clean

    @validates("term_scope")
    def validate_term_scope(self, key: str, value: list[str] | None) -> list[str]:
        if value is None:
            return []
        clean: list[str] = []
        for item in value:
            normalized = str(item).strip()
            if normalized:
                clean.append(normalized)
        return clean

    @validates("table_column_headers")
    def validate_table_column_headers(self, key: str, value: list[str] | None) -> list[str]:
        if value is None:
            return []
        return [str(item).strip() for item in value if str(item).strip()]

    @validates("ordinal")
    def validate_ordinal(self, key: str, value: int) -> int:
        if value < 0:
            raise ValueError("ordinal must be non-negative.")
        return value

    @validates("embedding_dimensions")
    def validate_embedding_dimensions(self, key: str, value: int | None) -> int | None:
        if value is not None and value != EMBEDDING_DIMENSIONS:
            raise ValueError(f"embedding_dimensions must be {EMBEDDING_DIMENSIONS}.")
        return value

    def __repr__(self) -> str:
        return (
            f"RetrievalChunk(id={self.id!r}, version_id={self.version_id!r}, "
            f"ordinal={self.ordinal!r}, section_ref={self.section_ref!r})"
        )
