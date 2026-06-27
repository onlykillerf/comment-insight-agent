from __future__ import annotations


class InMemoryVectorStore:
    """Simple vector store facade for local MVP and tests."""

    def __init__(self) -> None:
        self._vectors: dict[str, list[float]] = {}

    def upsert(self, vector_id: str, vector: list[float]) -> str:
        """Store a vector and return its id."""

        self._vectors[vector_id] = vector
        return vector_id

    def get(self, vector_id: str) -> list[float] | None:
        """Return a vector by id."""

        return self._vectors.get(vector_id)

