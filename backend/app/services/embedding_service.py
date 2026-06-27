from __future__ import annotations

import hashlib
import math
import re


class EmbeddingService:
    """Small deterministic embedding service used by the MVP.

    It keeps local demos lightweight while preserving the same interface that a
    sentence-transformers or remote embedding provider can implement later.
    """

    model_name = "hashing-embedding-v1"

    def embed_texts(self, texts: list[str], dimensions: int = 64) -> list[list[float]]:
        """Convert texts to normalized hashing vectors."""

        return [self._embed(text, dimensions) for text in texts]

    def _embed(self, text: str, dimensions: int) -> list[float]:
        vector = [0.0] * dimensions
        tokens = re.findall(r"[\w\u4e00-\u9fff]+", text.lower())
        for token in tokens or [text]:
            digest = hashlib.sha1(token.encode("utf-8")).hexdigest()
            index = int(digest[:8], 16) % dimensions
            vector[index] += 1.0
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [round(value / norm, 6) for value in vector]


def cosine_similarity(left: list[float], right: list[float]) -> float:
    """Return cosine similarity for normalized or raw vectors."""

    numerator = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left)) or 1.0
    right_norm = math.sqrt(sum(b * b for b in right)) or 1.0
    return numerator / (left_norm * right_norm)

