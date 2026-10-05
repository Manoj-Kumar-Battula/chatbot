from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from urllib.parse import urlparse, urlunparse


@dataclass(frozen=True)
class CanonicalSourceIdentity:
    canonical_url: str
    source_type: str
    host: str


@dataclass
class SourceVersionRecord:
    source_id: str
    version_id: str
    content_sha256: str
    is_current: bool = False
    supersedes_version_id: str | None = None
    freshness_status: str = "unknown"


def canonicalize_pnw_url(url: str) -> str:
    if not isinstance(url, str):
        raise ValueError("url must be a string")

    candidate = url.strip()
    if not candidate:
        raise ValueError("url cannot be blank")

    parsed = urlparse(candidate)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("url must use http or https")
    if not parsed.hostname:
        raise ValueError("url must include a host")
    if parsed.username or parsed.password:
        raise ValueError("url must not include credentials")

    host = parsed.hostname.lower()
    if host != "pnw.edu" and not host.endswith(".pnw.edu"):
        raise ValueError("source URL must resolve to an official PNW domain")

    try:
        port = parsed.port
    except ValueError as exc:
        raise ValueError("url contains an invalid port") from exc
    if port not in (None, 80 if parsed.scheme == "http" else 443):
        raise ValueError("official source URL must use its standard HTTP(S) port")

    normalized_path = parsed.path.rstrip("/") or "/"
    return urlunparse((parsed.scheme.lower(), host, normalized_path, "", "", ""))


def canonical_source_identity(url: str, *, source_type: str = "webpage") -> CanonicalSourceIdentity:
    canonical = canonicalize_pnw_url(url)
    parsed = urlparse(canonical)
    host = parsed.netloc.lower().split(":")[0]
    source_type = str(source_type).strip().lower() or "webpage"
    return CanonicalSourceIdentity(canonical_url=canonical, source_type=source_type, host=host)


def compute_content_hash(payload: str | bytes) -> str:
    if isinstance(payload, str):
        data = payload.encode("utf-8")
    else:
        data = payload
    return sha256(data).hexdigest()


def select_current_version(versions: list[SourceVersionRecord]) -> SourceVersionRecord | None:
    if not versions:
        return None
    current = [version for version in versions if version.is_current]
    if current:
        return current[0]
    return versions[-1]


class VersionRegistry:
    def __init__(self) -> None:
        self._versions_by_source: dict[str, list[SourceVersionRecord]] = {}

    def register_version(
        self,
        *,
        source_id: str,
        version_id: str,
        content: str | bytes,
        freshness_status: str = "unknown",
    ) -> SourceVersionRecord:
        if not source_id:
            raise ValueError("source_id is required")
        if not version_id:
            raise ValueError("version_id is required")

        hash_value = compute_content_hash(content)
        existing = self._versions_by_source.setdefault(source_id, [])
        match = next((item for item in existing if item.content_sha256 == hash_value), None)
        if match is not None:
            match.is_current = True
            return match

        current = select_current_version(existing)
        record = SourceVersionRecord(
            source_id=source_id,
            version_id=version_id,
            content_sha256=hash_value,
            is_current=True,
            supersedes_version_id=current.version_id if current else None,
            freshness_status=freshness_status,
        )

        for item in existing:
            item.is_current = False
        existing.append(record)
        return record

    def get_current_version(self, source_id: str) -> SourceVersionRecord | None:
        return select_current_version(self._versions_by_source.get(source_id, []))

    def versions_for_source(self, source_id: str) -> list[SourceVersionRecord]:
        return list(self._versions_by_source.get(source_id, []))
