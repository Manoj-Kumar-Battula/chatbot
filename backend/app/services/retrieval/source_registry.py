from __future__ import annotations

from app.corpus.versioning import SourceVersionRecord, VersionRegistry, canonical_source_identity


class SourceRegistry:
    def __init__(self) -> None:
        self._registry = VersionRegistry()

    def register_version(
        self,
        *,
        source_id: str,
        version_id: str,
        content: str | bytes,
        url: str,
        source_type: str = "webpage",
        freshness_status: str = "unknown",
    ) -> SourceVersionRecord:
        identity = canonical_source_identity(url, source_type=source_type)
        if identity.canonical_url and not source_id:
            raise ValueError("source_id is required when a canonical source URL is used")
        return self._registry.register_version(
            source_id=source_id,
            version_id=version_id,
            content=content,
            freshness_status=freshness_status,
        )

    def current_version(self, source_id: str) -> SourceVersionRecord | None:
        return self._registry.get_current_version(source_id)

    def versions_for_source(self, source_id: str) -> list[SourceVersionRecord]:
        return self._registry.versions_for_source(source_id)


def get_current_source_version(registry: SourceRegistry, source_id: str) -> SourceVersionRecord | None:
    return registry.current_version(source_id)
