from __future__ import annotations

import io
import re
from dataclasses import dataclass, field
from datetime import date
from html.parser import HTMLParser
from typing import Any


VALID_SOURCE_TYPES = {"webpage", "pdf", "catalog_entry", "policy", "schedule", "linked_document", "office_page"}


@dataclass
class ParsedLink:
    label: str
    url: str
    context: str = ""


@dataclass
class ParsedTable:
    caption: str | None = None
    headers: list[str] = field(default_factory=list)
    rows: list[list[str]] = field(default_factory=list)
    table_id: str | None = None


@dataclass
class StructuredDocument:
    source_url: str
    source_type: str
    title: str
    canonical_url: str | None = None
    text: str = ""
    headings: list[str] = field(default_factory=list)
    links: list[ParsedLink] = field(default_factory=list)
    tables: list[ParsedTable] = field(default_factory=list)
    sections: list[dict[str, Any]] = field(default_factory=list)
    document_date: date | None = None
    parser_name: str = ""
    parser_version: str = "unknown"
    extraction_status: str = "complete"
    campus_applicability: list[str] = field(default_factory=list)
    topic_tags: list[str] = field(default_factory=list)
    freshness_status: str = "unknown"
    page_count: int = 0

    def as_dict(self) -> dict[str, Any]:
        return {
            "source_url": self.source_url,
            "source_type": self.source_type,
            "title": self.title,
            "canonical_url": self.canonical_url,
            "text": self.text,
            "headings": self.headings,
            "links": [link.__dict__ for link in self.links],
            "tables": [table.__dict__ for table in self.tables],
            "sections": self.sections,
            "document_date": self.document_date.isoformat() if self.document_date else None,
            "parser_name": self.parser_name,
            "parser_version": self.parser_version,
            "extraction_status": self.extraction_status,
            "campus_applicability": self.campus_applicability,
            "topic_tags": self.topic_tags,
            "freshness_status": self.freshness_status,
            "page_count": self.page_count,
        }


class _HTMLContentParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title = ""
        self.canonical_url: str | None = None
        self.headings: list[str] = []
        self.paragraphs: list[str] = []
        self.links: list[ParsedLink] = []
        self.tables: list[ParsedTable] = []
        self.body_text: list[str] = []
        self.current_table: ParsedTable | None = None
        self.current_row: list[str] = []
        self._capture_stack: list[tuple[str, list[str], str | None]] = []
        self._suppressed_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {k: v for k, v in attrs}
        tag_name = tag.lower()
        if tag_name in {"head", "script", "style", "noscript"}:
            self._suppressed_depth += 1
        elif tag_name == "link" and "canonical" in (attrs_dict.get("rel") or "").lower().split():
            self.canonical_url = attrs_dict.get("href")
        elif tag_name == "table":
            self.current_table = ParsedTable(caption=None, headers=[], rows=[], table_id=attrs_dict.get("id"))
        elif tag_name == "tr":
            self.current_row = []
        elif tag_name in {"title", "h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "a", "th", "td"}:
            self._capture_stack.append((tag_name, [], attrs_dict.get("href")))

    def handle_endtag(self, tag: str) -> None:
        tag_name = tag.lower()
        if tag_name in {"head", "script", "style", "noscript"}:
            self._suppressed_depth = max(0, self._suppressed_depth - 1)
        for index in range(len(self._capture_stack) - 1, -1, -1):
            capture_tag, parts, href = self._capture_stack[index]
            if capture_tag != tag_name:
                continue
            del self._capture_stack[index]
            value = re.sub(r"\s+", " ", "".join(parts)).strip()
            if tag_name == "title":
                self.title = value
            elif tag_name in {"h1", "h2", "h3", "h4", "h5", "h6"} and value:
                self.headings.append(value)
            elif tag_name in {"p", "li"} and value:
                self.paragraphs.append(value)
            elif tag_name == "a" and href and value:
                self.links.append(ParsedLink(label=value, url=href, context=""))
            elif tag_name in {"th", "td"} and self.current_table is not None:
                self.current_row.append(value)
            break
        if tag_name == "table":
            if self.current_table is not None:
                if self.current_table.rows and not self.current_table.headers:
                    self.current_table.headers = self.current_table.rows.pop(0)
                self.tables.append(self.current_table)
                self.current_table = None
        elif tag_name == "tr" and self.current_table is not None:
            if self.current_row:
                self.current_table.rows.append(self.current_row)
            self.current_row = []

    def handle_data(self, data: str) -> None:
        for _, parts, _ in self._capture_stack:
            parts.append(data)
        if not self._suppressed_depth and data.strip():
            self.body_text.append(data)


def _normalize_source_type(source_type: str | None) -> str:
    normalized = (source_type or "webpage").strip().lower()
    if normalized not in VALID_SOURCE_TYPES:
        raise ValueError(f"Unsupported source_type {source_type!r}; expected one of {sorted(VALID_SOURCE_TYPES)}")
    return normalized


def _extract_headings(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip() and not line.strip().startswith("http")][:20]


def _build_sections(title: str, headings: list[str], paragraphs: list[str]) -> list[dict[str, Any]]:
    sections: list[dict[str, Any]] = []
    if headings:
        for index, heading in enumerate(headings):
            start = index
            end = index + 1 if index + 1 < len(headings) else len(paragraphs)
            content = "\n\n".join(paragraphs[start:end])
            sections.append({"heading": heading, "text": content})
    if not sections and title:
        sections.append({"heading": title, "text": " ".join(paragraphs)[:2000]})
    return sections


def load_html_document(
    source_url: str,
    raw_html: str,
    *,
    source_type: str | None = None,
    title: str | None = None,
    campus_applicability: list[str] | None = None,
    topic_tags: list[str] | None = None,
    freshness_status: str = "unknown",
) -> StructuredDocument:
    parser = _HTMLContentParser()
    parser.feed(raw_html)
    parser.close()

    effective_title = (title or parser.title or source_url).strip() or "Untitled PNW source"
    paragraphs = parser.paragraphs or []
    body_text = re.sub(r"\s+", " ", " ".join(parser.body_text)).strip()
    headings = parser.headings or ([effective_title] if paragraphs or body_text else [])
    text = "\n\n".join(paragraphs) if paragraphs else body_text
    doc = StructuredDocument(
        source_url=source_url,
        source_type=_normalize_source_type(source_type),
        title=effective_title,
        canonical_url=parser.canonical_url,
        text=text,
        headings=headings,
        links=parser.links,
        tables=parser.tables,
        sections=_build_sections(effective_title, headings, paragraphs or ([body_text] if body_text else [])),
        parser_name="html_parser",
        parser_version="1.0",
        extraction_status="complete" if text.strip() or parser.tables else "partial",
        campus_applicability=campus_applicability or [],
        topic_tags=topic_tags or [],
        freshness_status=freshness_status,
    )
    return doc


def load_pdf_document(
    source_url: str,
    raw_pdf: bytes,
    *,
    source_type: str | None = None,
    title: str | None = None,
    campus_applicability: list[str] | None = None,
    topic_tags: list[str] | None = None,
    freshness_status: str = "unknown",
) -> StructuredDocument:
    try:
        from pypdf import PdfReader
    except Exception:
        return StructuredDocument(
            source_url=source_url,
            source_type=_normalize_source_type(source_type),
            title=(title or source_url).strip() or "Untitled PDF source",
            canonical_url=None,
            text="",
            headings=[],
            links=[],
            tables=[],
            sections=[],
            parser_name="pypdf",
            parser_version="unavailable",
            extraction_status="failed",
            campus_applicability=campus_applicability or [],
            topic_tags=topic_tags or [],
            freshness_status=freshness_status,
            page_count=0,
        )

    reader = PdfReader(io.BytesIO(raw_pdf))
    pages: list[tuple[int, str]] = []
    for page_number, page in enumerate(reader.pages, start=1):
        extracted = page.extract_text() or ""
        normalized = " ".join(extracted.split())
        if normalized:
            pages.append((page_number, normalized))

    content = "\n\n".join(text for _, text in pages)
    headings = _extract_headings(content)
    sections = [
        {"heading": f"Page {page_number}", "text": text, "page_start": page_number, "page_end": page_number}
        for page_number, text in pages
    ]
    return StructuredDocument(
        source_url=source_url,
        source_type=_normalize_source_type(source_type),
        title=(title or source_url).strip() or "Untitled PDF source",
        canonical_url=None,
        text=content,
        headings=headings,
        links=[],
        tables=[],
        sections=sections or _build_sections((title or source_url or "PDF source"), headings, []),
        parser_name="pypdf",
        parser_version="latest",
        extraction_status="complete" if content.strip() else "partial",
        campus_applicability=campus_applicability or [],
        topic_tags=topic_tags or [],
        freshness_status=freshness_status,
        page_count=len(reader.pages),
    )
