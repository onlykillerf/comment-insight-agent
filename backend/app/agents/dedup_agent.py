from __future__ import annotations

import hashlib
import re

from app.services.embedding_service import EmbeddingService, cosine_similarity


class DeduplicationAgent:
    """Remove exact, near and semantic duplicate comments."""

    def __init__(self, embedding_service: EmbeddingService | None = None) -> None:
        self.embedding_service = embedding_service or EmbeddingService()

    def run(self, comments: list[dict], threshold: float = 0.92) -> list[dict]:
        """Mark duplicate comments and keep all rows for traceability."""

        seen_hashes: dict[str, str] = {}
        vectors = self.embedding_service.embed_texts([comment["cleaned_content"] for comment in comments])
        accepted: list[tuple[str, list[float]]] = []
        for index, comment in enumerate(comments):
            normalized = self._normalize_for_hash(comment["cleaned_content"])
            exact_hash = hashlib.sha1(normalized.encode("utf-8")).hexdigest()
            duplicate_group_id = seen_hashes.get(exact_hash)
            if not duplicate_group_id:
                duplicate_group_id = self._near_duplicate_group(normalized, accepted, vectors[index], threshold)
            if duplicate_group_id:
                comment["is_duplicate"] = True
                comment["duplicate_group_id"] = duplicate_group_id
            else:
                seen_hashes[exact_hash] = exact_hash[:12]
                accepted.append((exact_hash[:12], vectors[index]))
                comment["duplicate_group_id"] = exact_hash[:12]
            comment["embedding"] = vectors[index]
        return comments

    def _normalize_for_hash(self, text: str) -> str:
        return re.sub(r"\W+", "", text.lower())

    def _near_duplicate_group(self, text: str, accepted: list[tuple[str, list[float]]], vector: list[float], threshold: float) -> str | None:
        if not accepted:
            return None
        for group_id, existing in accepted:
            if cosine_similarity(vector, existing) >= threshold:
                return group_id
        return None

