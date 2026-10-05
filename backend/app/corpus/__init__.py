from .chunking import ChunkDraft, chunk_document
from .embeddings import DEFAULT_EMBEDDING_MODEL, EMBEDDING_DIMENSIONS, LocalSentenceTransformerEmbedder
from .ingestion import IngestionSummary, load_corpus_documents, persist_corpus
from .loaders import StructuredDocument, load_html_document, load_pdf_document
from .versioning import (
    CanonicalSourceIdentity,
    SourceVersionRecord,
    VersionRegistry,
    canonical_source_identity,
    canonicalize_pnw_url,
    compute_content_hash,
    select_current_version,
)

__all__ = [
    "CanonicalSourceIdentity",
    "ChunkDraft",
    "DEFAULT_EMBEDDING_MODEL",
    "EMBEDDING_DIMENSIONS",
    "IngestionSummary",
    "LocalSentenceTransformerEmbedder",
    "SourceVersionRecord",
    "StructuredDocument",
    "VersionRegistry",
    "canonical_source_identity",
    "canonicalize_pnw_url",
    "chunk_document",
    "compute_content_hash",
    "load_corpus_documents",
    "load_html_document",
    "load_pdf_document",
    "persist_corpus",
    "select_current_version",
]
