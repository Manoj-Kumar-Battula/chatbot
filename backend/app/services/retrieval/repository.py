from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.official_source import OfficialSource
from app.models.official_source_version import OfficialSourceVersion
from app.models.retrieval_chunk import RetrievalChunk


@dataclass
class RetrievalFilter:
    campus: str | None = None
    term: str | None = None
    source_type: str | None = None
    current_only: bool = True
    min_similarity: float | None = None
    model_name: str | None = None


class SourceRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_sources(self, *, campus: str | None = None, source_type: str | None = None) -> list[OfficialSource]:
        stmt = select(OfficialSource)
        if source_type:
            stmt = stmt.where(OfficialSource.source_type == source_type)
        if campus:
            stmt = stmt.where(OfficialSource.campus_applicability.contains([campus]))
        return list(self.db.execute(stmt).scalars().all())

    def list_current_versions(self, *, source_ids: list[str] | None = None) -> list[OfficialSourceVersion]:
        stmt = select(OfficialSourceVersion).where(OfficialSourceVersion.is_current.is_(True))
        if source_ids:
            stmt = stmt.where(OfficialSourceVersion.source_id.in_(source_ids))
        return list(self.db.execute(stmt).scalars().all())

    def list_chunks(
        self,
        *,
        campus: str | None = None,
        term: str | None = None,
        source_ids: list[str] | None = None,
        current_only: bool = True,
        min_similarity: float | None = None,
        model_name: str | None = None,
    ) -> list[RetrievalChunk]:
        stmt = select(RetrievalChunk)
        if current_only:
            stmt = stmt.join(OfficialSourceVersion).where(OfficialSourceVersion.is_current.is_(True))
        if source_ids:
            stmt = stmt.where(RetrievalChunk.version_id.in_(source_ids))
        if campus:
            stmt = stmt.where(RetrievalChunk.campus_scope.contains([campus]))
        if term:
            stmt = stmt.where(RetrievalChunk.term_scope.contains([term]))
        if model_name:
            stmt = stmt.where(RetrievalChunk.embedding_model == model_name)
        return list(self.db.execute(stmt).scalars().all())

    def validate_embedding_dimensions(self, embedding: list[float] | None, *, expected_dimensions: int | None = None) -> bool:
        if embedding is None:
            return True
        if expected_dimensions is None:
            return True
        return len(embedding) == expected_dimensions

    def hybrid_query(
        self,
        *,
        query_text: str,
        filters: RetrievalFilter | None = None,
        embedding: list[float] | None = None,
        expected_dimensions: int | None = None,
    ) -> list[RetrievalChunk]:
        if not query_text:
            raise ValueError("query_text cannot be blank")

        if expected_dimensions is not None and embedding is not None:
            if not self.validate_embedding_dimensions(embedding, expected_dimensions=expected_dimensions):
                raise ValueError("embedding dimensions do not match the expected vector size")

        filter_values = filters or RetrievalFilter()
        chunks = self.list_chunks(
            campus=filter_values.campus,
            term=filter_values.term,
            current_only=filter_values.current_only,
            min_similarity=filter_values.min_similarity,
            model_name=filter_values.model_name,
        )

        if filter_values.source_type:
            chunks = [chunk for chunk in chunks if chunk.version and chunk.version.source.source_type == filter_values.source_type]

        if filter_values.min_similarity is not None:
            chunks = [chunk for chunk in chunks if chunk.embedding is not None]

        return chunks
