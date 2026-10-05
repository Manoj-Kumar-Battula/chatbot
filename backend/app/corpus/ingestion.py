from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import date
from hashlib import sha256
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.corpus.chunking import ChunkDraft, chunk_document
from app.corpus.embeddings import EMBEDDING_DIMENSIONS, Embedder, validate_embeddings
from app.corpus.loaders import StructuredDocument, load_html_document, load_pdf_document
from app.corpus.versioning import canonical_source_identity
from app.models.official_source import OfficialSource
from app.models.official_source_version import OfficialSourceVersion
from app.models.retrieval_chunk import RetrievalChunk

SUPPORTED_EXTENSIONS = {".pdf", ".html", ".htm"}
VALID_FRESHNESS = {"current", "stale", "unknown"}


@dataclass(frozen=True)
class LoadedCorpusDocument:
    path: Path
    raw_content: bytes
    document: StructuredDocument
    metadata: dict[str, Any]

    @property
    def content_sha256(self) -> str:
        return sha256(self.raw_content).hexdigest()


@dataclass
class IngestionSummary:
    documents: int = 0
    sources_created: int = 0
    versions_created: int = 0
    chunks_created: int = 0
    chunks_reused: int = 0
    embedding_model: str = ""
    embedding_dimensions: int = EMBEDDING_DIMENSIONS

    @property
    def chunks(self) -> int:
        return self.chunks_created + self.chunks_reused

    @property
    def stored_records(self) -> int:
        return self.sources_created + self.versions_created + self.chunks_created


def _read_manifest(corpus_dir: Path, manifest_name: str) -> dict[str, dict[str, Any]]:
    manifest_path = corpus_dir / manifest_name
    if not manifest_path.exists():
        return {}
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{manifest_path} must contain an object mapping relative file paths to metadata.")

    entries: dict[str, dict[str, Any]] = {}
    for relative_path, metadata in data.items():
        if not isinstance(relative_path, str) or not isinstance(metadata, dict):
            raise ValueError(f"Invalid entry in {manifest_path}: each key must be a path and each value an object.")
        entries[Path(relative_path).as_posix()] = metadata
    return entries


def _metadata_for_file(
    path: Path,
    corpus_dir: Path,
    manifest: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    relative_path = path.relative_to(corpus_dir).as_posix()
    metadata = dict(manifest.get(relative_path, {}))

    sidecars = [path.with_name(path.name + ".json"), path.with_suffix(".json")]
    for sidecar in sidecars:
        if sidecar.is_file():
            sidecar_data = json.loads(sidecar.read_text(encoding="utf-8"))
            if not isinstance(sidecar_data, dict):
                raise ValueError(f"{sidecar} must contain a JSON object.")
            metadata = {**sidecar_data, **metadata}
            break
    return metadata


def _metadata_date(value: Any) -> date | None:
    if value in (None, ""):
        return None
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except ValueError as exc:
        raise ValueError(f"document_date must use YYYY-MM-DD format, got {value!r}.") from exc


def load_corpus_documents(
    corpus_dir: Path,
    *,
    min_documents: int = 3,
    manifest_name: str = "manifest.json",
) -> list[LoadedCorpusDocument]:
    corpus_dir = corpus_dir.expanduser().resolve()
    if not corpus_dir.is_dir():
        raise ValueError(f"Corpus directory does not exist or is not a directory: {corpus_dir}")

    paths = sorted(
        path
        for path in corpus_dir.rglob("*")
        if path.is_file()
        and path.suffix.lower() in SUPPORTED_EXTENSIONS
        and not any(part.startswith(".") for part in path.relative_to(corpus_dir).parts)
    )
    if min_documents < 1:
        raise ValueError("min_documents must be positive.")
    if len(paths) < min_documents:
        raise ValueError(
            f"Found {len(paths)} PDF/HTML documents in {corpus_dir}; at least {min_documents} are required."
        )

    manifest = _read_manifest(corpus_dir, manifest_name)
    loaded: list[LoadedCorpusDocument] = []
    for path in paths:
        metadata = _metadata_for_file(path, corpus_dir, manifest)
        raw_content = path.read_bytes()
        extension = path.suffix.lower()
        source_type = metadata.get("source_type") or ("pdf" if extension == ".pdf" else "webpage")
        supplied_url = metadata.get("source_url") or metadata.get("canonical_url")
        parser_input_url = supplied_url or path.as_uri()
        title = str(metadata.get("title") or path.stem.replace("_", " ").replace("-", " ")).strip()
        common_metadata = {
            "source_type": source_type,
            "title": title,
            "campus_applicability": metadata.get("campus_applicability", ["unknown"]),
            "topic_tags": metadata.get("topic_tags", []),
            "freshness_status": metadata.get("freshness_status", "unknown"),
        }
        if extension == ".pdf":
            document = load_pdf_document(parser_input_url, raw_content, **common_metadata)
        else:
            document = load_html_document(
                parser_input_url,
                raw_content.decode("utf-8", errors="replace"),
                **common_metadata,
            )

        source_url = supplied_url or document.canonical_url
        if not source_url:
            raise ValueError(
                f"No official source URL found for {path}. Add source_url to manifest.json "
                "or an adjacent .json sidecar; HTML files may use <link rel=\"canonical\">."
            )
        identity = canonical_source_identity(str(source_url), source_type=str(source_type))
        if document.extraction_status == "failed" or not document.text.strip():
            raise ValueError(f"No extractable text found in {path} (parser status: {document.extraction_status}).")
        if document.freshness_status not in VALID_FRESHNESS:
            raise ValueError(f"Invalid freshness_status for {path}: {document.freshness_status!r}")
        if not isinstance(document.campus_applicability, list) or not isinstance(document.topic_tags, list):
            raise ValueError(f"campus_applicability and topic_tags must be lists for {path}.")
        if not all(isinstance(value, str) for value in document.campus_applicability + document.topic_tags):
            raise ValueError(f"campus_applicability and topic_tags entries must be strings for {path}.")
        document_terms = metadata.get("term_scope", [])
        if not isinstance(document_terms, list) or not all(isinstance(value, str) for value in document_terms):
            raise ValueError(f"term_scope must be a list of strings for {path}.")

        document.source_url = identity.canonical_url
        document.canonical_url = identity.canonical_url
        document.document_date = _metadata_date(metadata.get("document_date"))
        loaded.append(LoadedCorpusDocument(path, raw_content, document, metadata))

    return loaded


def _retrieval_chunk(version_id: str, draft: ChunkDraft, vector: list[float], model_name: str) -> RetrievalChunk:
    return RetrievalChunk(
        version_id=version_id,
        ordinal=draft.ordinal,
        text=draft.text,
        heading_path=draft.heading_path,
        section_ref=draft.section_ref,
        page_start=draft.page_start,
        page_end=draft.page_end,
        html_anchor=draft.html_anchor,
        link_targets=draft.link_targets,
        campus_scope=draft.campus_scope,
        term_scope=draft.term_scope,
        course_code=draft.course_code,
        event_type=draft.event_type,
        table_id=draft.table_id,
        table_row_key=draft.table_row_key,
        table_column_headers=draft.table_column_headers,
        embedding_model=model_name,
        embedding_dimensions=EMBEDDING_DIMENSIONS,
        embedding=vector,
        search_text=draft.text,
    )


def persist_corpus(
    session: Session,
    documents: list[LoadedCorpusDocument],
    embedder: Embedder,
    *,
    max_words: int = 350,
    overlap_words: int = 60,
    term_scope: list[str] | None = None,
) -> IngestionSummary:
    if embedder.dimensions != EMBEDDING_DIMENSIONS:
        raise ValueError(
            f"Embedding model dimensions are {embedder.dimensions}; PostgreSQL schema requires {EMBEDDING_DIMENSIONS}."
        )

    summary = IngestionSummary(documents=len(documents), embedding_model=embedder.model_name)
    for item in documents:
        document = item.document
        source_url = document.canonical_url or document.source_url
        identity = canonical_source_identity(source_url, source_type=document.source_type)
        source = session.scalar(select(OfficialSource).where(OfficialSource.canonical_url == identity.canonical_url))
        if source is None:
            source = OfficialSource(
                canonical_url=identity.canonical_url,
                title=document.title[:512],
                source_type=document.source_type,
                campus_applicability=document.campus_applicability or ["unknown"],
                topic_tags=document.topic_tags,
                freshness_status=document.freshness_status,
                availability_status="available",
            )
            session.add(source)
            session.flush()
            summary.sources_created += 1
        else:
            source.title = document.title[:512]
            source.source_type = document.source_type
            source.campus_applicability = document.campus_applicability or ["unknown"]
            source.topic_tags = document.topic_tags
            source.freshness_status = document.freshness_status
            source.availability_status = "available"

        version = session.scalar(
            select(OfficialSourceVersion).where(
                OfficialSourceVersion.source_id == source.id,
                OfficialSourceVersion.content_sha256 == item.content_sha256,
            )
        )
        if version is not None:
            for source_version in session.scalars(
                select(OfficialSourceVersion).where(OfficialSourceVersion.source_id == source.id)
            ).all():
                source_version.is_current = source_version.id == version.id
            version.freshness_status = document.freshness_status
            source.current_version_id = version.id
            existing_chunks = session.scalar(
                select(RetrievalChunk.id).where(RetrievalChunk.version_id == version.id).limit(1)
            )
            if existing_chunks is None:
                raise ValueError(
                    f"Version {version.id} exists without retrieval chunks; refusing to report an incomplete import as successful."
                )
            summary.chunks_reused += len(
                session.scalars(select(RetrievalChunk.id).where(RetrievalChunk.version_id == version.id)).all()
            )
            continue

        source_versions = session.scalars(
            select(OfficialSourceVersion).where(OfficialSourceVersion.source_id == source.id)
        ).all()
        previous_version = next((item for item in source_versions if item.is_current), None)
        for source_version in source_versions:
            source_version.is_current = False

        version = OfficialSourceVersion(
            id=str(uuid.uuid4()),
            source_id=source.id,
            content_sha256=item.content_sha256,
            document_date=document.document_date,
            parser_name=document.parser_name,
            parser_version=document.parser_version,
            extraction_status=document.extraction_status,
            freshness_status=document.freshness_status,
            is_current=True,
            supersedes_version_id=previous_version.id if previous_version else None,
            raw_object_uri=item.path.resolve().as_uri(),
            raw_content=item.raw_content,
        )
        session.add(version)
        session.flush()

        drafts = chunk_document(
            document,
            max_words=max_words,
            overlap_words=overlap_words,
            term_scope=item.metadata.get("term_scope", term_scope) or [],
        )
        if not drafts:
            raise ValueError(f"Chunking produced no retrieval chunks for {item.path}.")
        vectors = embedder.embed_documents([draft.text for draft in drafts])
        validate_embeddings(vectors, expected_count=len(drafts))
        session.add_all(
            _retrieval_chunk(version.id, draft, vector, embedder.model_name)
            for draft, vector in zip(drafts, vectors, strict=True)
        )
        session.flush()
        source.current_version_id = version.id
        summary.versions_created += 1
        summary.chunks_created += len(drafts)

    session.flush()
    return summary
