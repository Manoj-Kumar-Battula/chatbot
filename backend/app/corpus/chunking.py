from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.corpus.loaders.base import StructuredDocument


@dataclass(frozen=True)
class ChunkDraft:
    ordinal: int
    text: str
    heading_path: list[str] = field(default_factory=list)
    section_ref: str | None = None
    page_start: int | None = None
    page_end: int | None = None
    html_anchor: str | None = None
    link_targets: list[str] = field(default_factory=list)
    campus_scope: list[str] = field(default_factory=list)
    term_scope: list[str] = field(default_factory=list)
    course_code: str | None = None
    event_type: str | None = None
    table_id: str | None = None
    table_row_key: str | None = None
    table_column_headers: list[str] = field(default_factory=list)


def _sentences(text: str) -> list[str]:
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        return []
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", normalized) if part.strip()]


def _split_text(text: str, max_words: int, overlap_words: int) -> list[str]:
    if max_words <= 0:
        raise ValueError("max_words must be positive")
    if overlap_words < 0 or overlap_words >= max_words:
        raise ValueError("overlap_words must be non-negative and less than max_words")

    sentences = _sentences(text)
    chunks: list[str] = []
    current: list[str] = []
    current_words = 0

    for sentence in sentences:
        words = sentence.split()
        if len(words) > max_words:
            if current:
                chunks.append(" ".join(current).strip())
                current = []
                current_words = 0
            start = 0
            while start < len(words):
                end = min(start + max_words, len(words))
                chunks.append(" ".join(words[start:end]))
                if end == len(words):
                    break
                start = end - overlap_words if overlap_words else end
            current = []
            current_words = 0
            continue

        if current_words + len(words) > max_words:
            chunks.append(" ".join(current).strip())
            overlap_limit = max_words - len(words)
            overlap = " ".join(current).split()[-min(overlap_words, overlap_limit) :] if overlap_limit else []
            current = [" ".join(overlap)] if overlap else []
            current_words = len(overlap)
        current.append(sentence)
        current_words += len(words)

    if current:
        chunks.append(" ".join(current).strip())
    return [chunk for chunk in chunks if chunk]


def _table_row_text(headers: list[str], row: list[str]) -> str:
    if headers and len(headers) == len(row):
        return "; ".join(f"{header}: {value}" for header, value in zip(headers, row) if value.strip())
    return " | ".join(cell.strip() for cell in row if cell.strip())


def chunk_document(
    document: StructuredDocument,
    *,
    max_words: int = 350,
    overlap_words: int = 60,
    campus_scope: list[str] | None = None,
    term_scope: list[str] | None = None,
) -> list[ChunkDraft]:
    """Split structured content into overlapping text chunks without splitting table rows."""
    drafts: list[ChunkDraft] = []
    fallback_campus = campus_scope if campus_scope is not None else document.campus_applicability
    links = [link.url for link in document.links]
    sections = document.sections or [{"heading": document.title, "text": document.text}]

    for section in sections:
        heading = str(section.get("heading") or document.title).strip()
        section_text = str(section.get("text") or "").strip()
        heading_path = [item for item in [document.title, heading] if item]
        page_start = section.get("page_start")
        page_end = section.get("page_end", page_start)
        section_ref = section.get("section_ref") or heading or None

        for text in _split_text(section_text, max_words, overlap_words):
            drafts.append(
                ChunkDraft(
                    ordinal=len(drafts),
                    text=text,
                    heading_path=heading_path,
                    section_ref=section_ref,
                    page_start=page_start,
                    page_end=page_end,
                    link_targets=links,
                    campus_scope=list(fallback_campus),
                    term_scope=list(term_scope or []),
                )
            )

    heading_path = [document.title] if document.title else []
    for table_index, table in enumerate(document.tables):
        table_id = table.table_id or f"table-{table_index + 1}"
        for row_index, row in enumerate(table.rows):
            row_text = _table_row_text(table.headers, row)
            if not row_text:
                continue
            drafts.append(
                ChunkDraft(
                    ordinal=len(drafts),
                    text=row_text,
                    heading_path=heading_path,
                    section_ref=table.caption or table_id,
                    link_targets=links,
                    campus_scope=list(fallback_campus),
                    term_scope=list(term_scope or []),
                    table_id=table_id,
                    table_row_key=f"{table_id}:{row_index + 1}",
                    table_column_headers=list(table.headers),
                )
            )

    return drafts
