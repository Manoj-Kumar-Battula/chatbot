from __future__ import annotations

from typing import Any


VALID_CAMPUSES = {"Hammond", "Westville", "both", "unknown"}


def normalize_campus_value(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    if not normalized:
        return None
    lowered = normalized.lower()
    if lowered == "hammond":
        return "Hammond"
    if lowered == "westville":
        return "Westville"
    if lowered in {"both", "unknown"}:
        return lowered
    raise ValueError(f"Unsupported campus value: {value!r}")


def applies_to_campus(candidate_value: Any, required_campus: str | None) -> bool:
    if required_campus is None:
        return True
    values = candidate_value if isinstance(candidate_value, list) else [candidate_value]
    normalized_values = [normalize_campus_value(str(item)) for item in values if item is not None]
    if not normalized_values:
        return False
    campus = normalize_campus_value(required_campus)
    if campus is None:
        return True
    if campus == "both":
        return True
    return campus in normalized_values or "both" in normalized_values


def filter_official_sources(sources: list[Any], campus: str | None = None) -> list[Any]:
    if campus is None:
        return list(sources)
    return [source for source in sources if applies_to_campus(getattr(source, "campus_applicability", []), campus)]


def filter_retrieval_chunks(chunks: list[Any], campus: str | None = None) -> list[Any]:
    if campus is None:
        return list(chunks)
    return [chunk for chunk in chunks if applies_to_campus(getattr(chunk, "campus_scope", []), campus)]
