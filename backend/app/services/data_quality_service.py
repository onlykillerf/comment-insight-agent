from __future__ import annotations

from collections import Counter
from typing import Any


SMALL_SAMPLE_WARNING = "样本量较小，仅适合演示"


class DataQualityService:
    """Compute sample quality metrics for an analysis run."""

    def build(self, raw_comments: list[dict[str, Any]], comments: list[dict[str, Any]]) -> dict[str, Any]:
        """Return a DataQualityReport-compatible dictionary."""

        raw_count = len(raw_comments)
        clean_count = len(comments)
        dedup_count = len([comment for comment in comments if not comment.get("is_duplicate")])
        duplicate_count = max(0, clean_count - dedup_count)
        duplicate_ratio = round(duplicate_count / clean_count, 4) if clean_count else 0.0
        noise_ratio = round(max(0, raw_count - clean_count) / raw_count, 4) if raw_count else 0.0
        language_distribution = dict(Counter(comment.get("language", "unknown") for comment in comments))
        sample_confidence_level = self._confidence_level(dedup_count)
        warning = SMALL_SAMPLE_WARNING if dedup_count < 100 else ""
        return {
            "raw_count": raw_count,
            "clean_count": clean_count,
            "dedup_count": dedup_count,
            "duplicate_ratio": duplicate_ratio,
            "noise_ratio": noise_ratio,
            "language_distribution": language_distribution,
            "sample_confidence_level": sample_confidence_level,
            "warning": warning,
        }

    def _confidence_level(self, dedup_count: int) -> str:
        if dedup_count < 100:
            return "low"
        if dedup_count < 300:
            return "medium"
        return "high"
