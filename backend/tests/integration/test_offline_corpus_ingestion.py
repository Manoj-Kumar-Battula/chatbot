import copy
from dataclasses import replace
import json
import os
import uuid
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.corpus.embeddings import EMBEDDING_DIMENSIONS
from app.corpus.ingestion import load_corpus_documents, persist_corpus
from app.db.base import Base
from app.models.official_source import OfficialSource  # noqa: F401
from app.models.official_source_version import OfficialSourceVersion  # noqa: F401
from app.models.retrieval_chunk import RetrievalChunk  # noqa: F401


class _FixedEmbedder:
    model_name = "test-local-384"
    dimensions = EMBEDDING_DIMENSIONS

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[0.0] * self.dimensions for _ in texts]


def _write_corpus(corpus_dir: Path) -> None:
    corpus_dir.mkdir()
    manifest: dict[str, dict[str, object]] = {}
    for index in range(3):
        name = f"source-{index}.html"
        (corpus_dir / name).write_text(
            f"<html><head><title>Guide {index}</title></head><body>"
            f'<link rel="canonical" href="https://www.pnw.edu/integration/guide-{index}/">'
            f"<h1>Guide {index}</h1><p>Local integration document {index} includes useful information.</p>"
            "</body></html>",
            encoding="utf-8",
        )
        manifest[name] = {
            "source_url": f"https://www.pnw.edu/integration/guide-{index}/",
            "source_type": "webpage",
            "campus_applicability": ["both"],
            "topic_tags": ["integration"],
        }
    (corpus_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")


def test_three_document_ingestion_persists_and_is_idempotent(tmp_path: Path) -> None:
    database_url = os.environ.get("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("Set TEST_DATABASE_URL to a PostgreSQL database with pgvector to run the storage integration test.")

    engine = create_engine(database_url, pool_pre_ping=True)
    schema = f"ingest_test_{uuid.uuid4().hex}"
    corpus_dir = tmp_path / "corpus"
    _write_corpus(corpus_dir)
    documents = load_corpus_documents(corpus_dir)
    connection = engine.connect()
    try:
        if not connection.scalar(text("SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector')")):
            pytest.skip("The TEST_DATABASE_URL database does not have the pgvector extension installed.")
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))
        connection.commit()
        connection.execute(text(f'SET search_path TO "{schema}", public'))
        connection.commit()
        Base.metadata.create_all(bind=connection)

        with Session(bind=connection, expire_on_commit=False) as session:
            with session.begin():
                first = persist_corpus(session, documents, _FixedEmbedder())
                assert first.documents == 3
                assert first.sources_created == 3
                assert first.versions_created == 3
                assert first.chunks_created >= 3
                assert session.scalar(text("SELECT count(*) FROM official_source_versions WHERE is_current")) == 3

            with session.begin():
                second = persist_corpus(session, documents, _FixedEmbedder())
                assert second.versions_created == 0
                assert second.chunks_created == 0
                assert second.chunks_reused == first.chunks_created
                assert session.scalar(text("SELECT count(*) FROM official_source_versions WHERE is_current")) == 3

            changed_item = documents[0]
            changed_document = copy.deepcopy(changed_item.document)
            changed_document.text += " Updated source content."
            changed_document.sections[0]["text"] += " Updated source content."
            changed_item = replace(
                changed_item,
                raw_content=changed_item.raw_content + b" ",
                document=changed_document,
            )
            with session.begin():
                changed = persist_corpus(session, [changed_item], _FixedEmbedder())
                assert changed.sources_created == 0
                assert changed.versions_created == 1
                assert changed.chunks_created >= 1

            assert session.scalar(text("SELECT count(*) FROM official_sources")) == 3
            assert session.scalar(text("SELECT count(*) FROM official_source_versions")) == 4
            assert session.scalar(text("SELECT count(*) FROM retrieval_chunks")) == first.chunks_created + changed.chunks_created
            assert session.scalar(text("SELECT count(*) FROM official_source_versions WHERE raw_content IS NOT NULL")) == 4
            assert session.scalar(
                text(
                    "SELECT count(*) FROM official_source_versions v "
                    "JOIN official_sources s ON s.id = v.source_id "
                    "WHERE s.canonical_url = :canonical_url AND v.is_current"
                ),
                {"canonical_url": changed_document.canonical_url},
            ) == 1
            assert session.scalar(text("SELECT count(*) FROM official_source_versions WHERE is_current")) == 3
            assert session.scalar(
                text("SELECT count(*) FROM retrieval_chunks WHERE embedding_dimensions = 384 AND embedding IS NOT NULL")
            ) == first.chunks_created + changed.chunks_created
    finally:
        connection.rollback()
        connection.execute(text(f'SET search_path TO public'))
        connection.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
        connection.commit()
        connection.close()
        engine.dispose()
