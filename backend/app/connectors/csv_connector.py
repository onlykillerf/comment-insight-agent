from __future__ import annotations

import csv
from hashlib import sha1
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
                comments.append(
                    normalize_row(row, request.platform, request.semantic_query, request.field_mapping)
                )
                if len(comments) >= request.max_comments:
                    break
        return comments


def normalize_row(
    row: dict[str, object],
    fallback_platform: str,
    topic: str,
    field_mapping: dict[str, str] | None = None,
) -> NormalizedComment:
    mapping = field_mapping or {}

    def value(canonical: str, aliases: list[str]) -> str:
        source = mapping.get(canonical)
        candidates = [source] if source else aliases
        for candidate in candidates:
            if candidate and row.get(candidate) not in (None, ""):
                return str(row[candidate])
        return ""

    content = value("content", ["content", "comment", "comment_text", "review_text", "text"])
    generated_id = sha1(content.encode("utf-8")).hexdigest()[:16]
    return {
        "id": value("id", ["id", "comment_id", "commentId", "cid"]) or f"upload-{generated_id}",
        "platform": value("platform", ["platform", "source_platform"]) or fallback_platform,
        "topic": value("topic", ["topic", "title", "note_title"]) or topic,
        "content": content,
        "author_hash": value("author_hash", ["author_hash", "user_hash", "user_id", "author_id"]) or "upload-user",
        "like_count": _safe_int(value("like_count", ["like_count", "likes", "liked_count", "digg_count"])),
        "reply_count": _safe_int(value("reply_count", ["reply_count", "replies", "sub_comment_count"])),
        "publish_time": value("publish_time", ["publish_time", "created_at", "create_time", "review_time"]),
        "source_url": value("source_url", ["source_url", "url", "note_url", "detail_url"]),
        "parent_id": value("parent_id", ["parent_id", "parent_comment_id", "root_comment_id"]) or None,
        "image_urls": [],
        "image_analysis": {},
        "metadata": {"source": "csv"},
    }


def _safe_int(value: str) -> int:
    try:
        return int(float(value or 0))
    except (TypeError, ValueError):
        return 0
