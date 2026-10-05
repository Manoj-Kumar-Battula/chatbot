from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Protocol

from app.models.retrieval_chunk import EMBEDDING_DIMENSIONS

DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


class Embedder(Protocol):
    model_name: str
    dimensions: int

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]: ...


class LocalSentenceTransformerEmbedder:
    """Run Sentence Transformers locally; model weights are cached by the library."""

    def __init__(self, model_name: str = DEFAULT_EMBEDDING_MODEL) -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                "Local embeddings require sentence-transformers. Install backend/requirements.txt."
            ) from exc

        self.model_name = model_name
        self._model = SentenceTransformer(model_name, device="cpu")
        self.dimensions = int(self._model.get_sentence_embedding_dimension())
        if self.dimensions != EMBEDDING_DIMENSIONS:
            raise ValueError(
                f"Embedding model {model_name!r} produced {self.dimensions} dimensions; "
                f"the database schema requires {EMBEDDING_DIMENSIONS}."
            )

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        vectors = self._model.encode(
            list(texts),
            batch_size=32,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        results = [[float(value) for value in vector] for vector in vectors]
        validate_embeddings(results, expected_count=len(texts))
        return results


def validate_embeddings(vectors: Sequence[Sequence[float]], *, expected_count: int) -> None:
    if len(vectors) != expected_count:
        raise ValueError(f"Embedding count mismatch: expected {expected_count}, received {len(vectors)}.")
    for index, vector in enumerate(vectors):
        if len(vector) != EMBEDDING_DIMENSIONS:
            raise ValueError(
                f"Embedding {index} has {len(vector)} dimensions; expected {EMBEDDING_DIMENSIONS}."
            )
        if not all(math.isfinite(float(value)) for value in vector):
            raise ValueError(f"Embedding {index} contains a non-finite value.")
