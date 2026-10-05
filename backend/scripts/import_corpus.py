#!/usr/bin/env python3
"""Parse, chunk, locally embed, and store a directory of PNW source documents."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from app.config.settings import settings
from app.corpus.embeddings import DEFAULT_EMBEDDING_MODEL, LocalSentenceTransformerEmbedder
from app.corpus.ingestion import load_corpus_documents, persist_corpus


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Ingest PDF/HTML corpus files into PostgreSQL/pgvector using local sentence-transformer embeddings."
    )
    parser.add_argument("corpus_dir", type=Path, help="Directory containing at least three PDF/HTML documents.")
    parser.add_argument(
        "--database-url",
        default=settings.database_url,
        help="SQLAlchemy PostgreSQL URL (defaults to DATABASE_URL).",
    )
    parser.add_argument(
        "--embedding-model",
        default=DEFAULT_EMBEDDING_MODEL,
        help=f"Local Sentence Transformers model (default: {DEFAULT_EMBEDDING_MODEL}).",
    )
    parser.add_argument("--manifest", default="manifest.json", help="Corpus metadata manifest filename.")
    parser.add_argument("--chunk-words", type=int, default=350, help="Maximum words per text chunk.")
    parser.add_argument("--overlap-words", type=int, default=60, help="Word overlap between adjacent text chunks.")
    parser.add_argument("--term", action="append", dest="terms", help="Optional term scope; may be repeated.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        documents = load_corpus_documents(
            args.corpus_dir,
            manifest_name=args.manifest,
        )
    except (OSError, ValueError, UnicodeError) as exc:
        parser.error(str(exc))

    if args.chunk_words <= 0 or args.overlap_words < 0 or args.overlap_words >= args.chunk_words:
        parser.error("--chunk-words must be positive and --overlap-words must be between 0 and chunk-words - 1.")

    embedder = LocalSentenceTransformerEmbedder(args.embedding_model)
    engine = create_engine(args.database_url, pool_pre_ping=True)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    try:
        with session_factory.begin() as session:
            summary = persist_corpus(
                session,
                documents,
                embedder,
                max_words=args.chunk_words,
                overlap_words=args.overlap_words,
                term_scope=args.terms,
            )
    except (SQLAlchemyError, ValueError, RuntimeError) as exc:
        parser.error(f"Ingestion failed: {exc}")
    finally:
        engine.dispose()

    print("Corpus ingestion complete")
    print(f"  Documents processed: {summary.documents}")
    print(f"  Chunks produced: {summary.chunks}")
    print(f"  Embedding model: {summary.embedding_model}")
    print(f"  Embedding dimensions: {summary.embedding_dimensions}")
    print(f"  Sources created: {summary.sources_created}")
    print(f"  Versions created: {summary.versions_created}")
    print(f"  Chunk records created: {summary.chunks_created}")
    print(f"  Existing chunk records reused: {summary.chunks_reused}")
    print(f"  New records stored: {summary.stored_records}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
