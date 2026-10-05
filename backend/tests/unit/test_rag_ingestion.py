import json
import sys
from types import SimpleNamespace
from pathlib import Path

import pytest

from app.corpus.chunking import chunk_document
from app.corpus.embeddings import EMBEDDING_DIMENSIONS, LocalSentenceTransformerEmbedder, validate_embeddings
from app.corpus.ingestion import load_corpus_documents
from app.corpus.loaders import ParsedTable, StructuredDocument, load_html_document, load_pdf_document


def _minimal_pdf(text: str) -> bytes:
    command = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET\n".encode("ascii")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(command)).encode("ascii") + b" >>\nstream\n" + command + b"endstream",
    ]
    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{index} 0 obj\n".encode("ascii"))
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")
    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(offsets)}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    pdf.extend(
        f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("ascii")
    )
    return bytes(pdf)


def _write_three_source_documents(corpus_dir: Path) -> None:
    corpus_dir.mkdir()
    manifest = {}
    for index in range(2):
        relative_path = f"pages/source-{index}.html"
        path = corpus_dir / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "<html><head><title>PNW Guide</title>"
            f'<link rel="canonical" href="https://www.pnw.edu/demo/source-{index}/">'
            "</head><body><h1>Student services</h1>"
            "<p>Students can contact the office for help. "
            "<strong>Bring the required documents.</strong></p>"
            "<ul><li>Submit the request before the deadline.</li></ul>"
            "<table><tr><th>Campus</th><th>Office</th></tr>"
            "<tr><td>Hammond</td><td>Student services</td></tr></table>"
            "</body></html>",
            encoding="utf-8",
        )
        manifest[relative_path] = {
            "source_url": f"https://www.pnw.edu/demo/source-{index}/",
            "source_type": "webpage",
            "campus_applicability": ["both"],
            "topic_tags": ["student services"],
        }
    pdf_path = corpus_dir / "catalog" / "programs.pdf"
    pdf_path.parent.mkdir(parents=True)
    pdf_path.write_bytes(_minimal_pdf("Program requirements are listed in the official catalog."))
    manifest["catalog/programs.pdf"] = {
        "source_url": "https://www.pnw.edu/demo/programs.pdf",
        "source_type": "pdf",
        "campus_applicability": ["unknown"],
        "topic_tags": ["catalog"],
        "document_date": "2026-01-01",
    }
    (corpus_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")


def test_existing_html_loader_preserves_source_structure() -> None:
    document = load_html_document(
        "https://www.pnw.edu/demo/",
        """
        <html><head><title>Guide</title><link rel="canonical" href="https://www.pnw.edu/demo/"></head>
        <body><h1>Overview</h1><p>Contact <strong>student services</strong>.</p>
        <table><tr><th>Campus</th><th>Office</th></tr><tr><td>Hammond</td><td>Help desk</td></tr></table>
        </body></html>
        """,
    )

    assert document.canonical_url == "https://www.pnw.edu/demo/"
    assert document.text == "Contact student services."
    assert document.tables[0].headers == ["Campus", "Office"]
    assert document.tables[0].rows == [["Hammond", "Help desk"]]


def test_existing_pdf_loader_preserves_page_location() -> None:
    document = load_pdf_document(
        "https://www.pnw.edu/demo/programs.pdf",
        _minimal_pdf("Program requirements are listed in the official catalog."),
        source_type="pdf",
    )

    assert "Program requirements" in document.text
    assert document.page_count == 1
    assert document.sections[0]["page_start"] == 1


def test_chunking_retains_heading_table_and_campus_metadata() -> None:
    document = StructuredDocument(
        source_url="https://www.pnw.edu/demo/",
        source_type="webpage",
        title="Student Guide",
        text="",
        sections=[
            {
                "heading": "Registration",
                "text": "Register early. Check your course schedule. Contact an advisor if you need help.",
                "page_start": 2,
                "page_end": 2,
            }
        ],
        tables=[
            ParsedTable(
                headers=["Campus", "Office"],
                rows=[["Hammond", "Registrar"]],
                table_id="registrar-offices",
            )
        ],
        campus_applicability=["Hammond"],
    )

    chunks = chunk_document(document, max_words=8, overlap_words=2)

    assert len(chunks) >= 2
    assert all(chunk.heading_path == ["Student Guide", "Registration"] for chunk in chunks[:-1])
    assert all(0 < len(chunk.text.split()) <= 8 for chunk in chunks)
    assert chunks[0].page_start == 2
    table_chunk = chunks[-1]
    assert table_chunk.table_id == "registrar-offices"
    assert table_chunk.table_row_key == "registrar-offices:1"
    assert table_chunk.table_column_headers == ["Campus", "Office"]
    assert table_chunk.text == "Campus: Hammond; Office: Registrar"
    assert table_chunk.campus_scope == ["Hammond"]


def test_corpus_loader_requires_and_loads_at_least_three_pdf_html_documents(tmp_path: Path) -> None:
    corpus_dir = tmp_path / "corpus"
    _write_three_source_documents(corpus_dir)

    documents = load_corpus_documents(corpus_dir, min_documents=3)

    assert len(documents) == 3
    assert all(item.document.canonical_url.startswith("https://www.pnw.edu/") for item in documents)
    html_documents = [item for item in documents if item.path.suffix == ".html"]
    pdf_document = next(item for item in documents if item.path.suffix == ".pdf")
    assert all("required documents" in item.document.text for item in html_documents)
    assert all(item.document.tables[0].headers == ["Campus", "Office"] for item in html_documents)
    assert "Program requirements" in pdf_document.document.text
    assert pdf_document.document.document_date.isoformat() == "2026-01-01"

    with pytest.raises(ValueError, match="at least 4 are required"):
        load_corpus_documents(corpus_dir, min_documents=4)


def test_embedding_validation_enforces_384_dimensions() -> None:
    validate_embeddings([[0.0] * EMBEDDING_DIMENSIONS], expected_count=1)
    with pytest.raises(ValueError, match="expected 384"):
        validate_embeddings([[0.0] * 1536], expected_count=1)


def test_local_sentence_transformer_runs_on_cpu_and_returns_384_dimensional_vectors(monkeypatch) -> None:
    class FakeSentenceTransformer:
        def __init__(self, model_name: str, *, device: str) -> None:
            assert model_name == "sentence-transformers/all-MiniLM-L6-v2"
            assert device == "cpu"

        @staticmethod
        def get_sentence_embedding_dimension() -> int:
            return EMBEDDING_DIMENSIONS

        @staticmethod
        def encode(texts: list[str], **kwargs) -> list[list[float]]:
            assert kwargs["normalize_embeddings"] is True
            return [[0.25] * EMBEDDING_DIMENSIONS for _ in texts]

    monkeypatch.setitem(
        sys.modules,
        "sentence_transformers",
        SimpleNamespace(SentenceTransformer=FakeSentenceTransformer),
    )
    embedder = LocalSentenceTransformerEmbedder()

    vectors = embedder.embed_documents(["A local embedding test."])

    assert embedder.model_name == "sentence-transformers/all-MiniLM-L6-v2"
    assert embedder.dimensions == 384
    assert len(vectors[0]) == 384
