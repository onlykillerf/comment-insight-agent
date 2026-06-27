from __future__ import annotations

import csv
from pathlib import Path

from app.connectors.base import FetchRequest, NormalizedComment


class CSVConnector:
    """Connector for user-provided CSV sample files."""

    name = "csv"

    def fetch_comments(self, request: FetchRequest) -> list[NormalizedComment]:
        """Read normalized comments from a CSV file."""

        if not request.source_path:
            raise ValueError("CSVConnector requires source_path")
        path = Path(request.source_path)
        comments: list[NormalizedComment] = []
        with path.open("r", encoding="utf-8-sig", newline="") as csvfile:
            for row in csv.DictReader(csvfile):
                comments.append(_normalize_row(row, request.platform, request.semantic_query))
                if len(comments) >= request.max_comments:
                    break
        return comments


def _normalize_row(row: dict[str, str], fallback_platform: str, topic: str) -> NormalizedComment:
    return {
        "id": row.get("id") or row.get("comment_id") or f"csv-{len(row)}-{hash(row.get('content', ''))}",
        "platform": row.get("platform") or fallback_platform,
        "topic": row.get("topic") or topic,
        "content": row.get("content") or row.get("comment") or row.get("review_text") or "",
        "author_hash": row.get("author_hash") or row.get("user_hash") or "csv-user",
        "like_count": int(row.get("like_count") or 0),
        "reply_count": int(row.get("reply_count") or 0),
        "publish_time": row.get("publish_time") or row.get("review_time") or "",
        "source_url": row.get("source_url") or "",
        "parent_id": row.get("parent_id") or None,
        "metadata": {"source": "csv"},
    }

