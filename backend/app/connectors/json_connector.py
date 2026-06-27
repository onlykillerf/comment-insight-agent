from __future__ import annotations

import json
from pathlib import Path

from app.connectors.base import FetchRequest, NormalizedComment


class JsonConnector:
    """Connector for user-provided JSON sample files."""

    name = "json"

    def fetch_comments(self, request: FetchRequest) -> list[NormalizedComment]:
        """Read normalized comments from a JSON list or object with comments."""

        if not request.source_path:
            raise ValueError("JsonConnector requires source_path")
        payload = json.loads(Path(request.source_path).read_text(encoding="utf-8"))
        rows = payload.get("comments", payload) if isinstance(payload, dict) else payload
        comments: list[NormalizedComment] = []
        for row in rows[: request.max_comments]:
            comments.append(
                {
                    "id": row.get("id") or row.get("comment_id"),
                    "platform": row.get("platform") or request.platform,
                    "topic": row.get("topic") or request.semantic_query,
                    "content": row.get("content") or row.get("comment") or "",
                    "author_hash": row.get("author_hash") or "json-user",
                    "like_count": int(row.get("like_count") or 0),
                    "reply_count": int(row.get("reply_count") or 0),
                    "publish_time": row.get("publish_time") or "",
                    "source_url": row.get("source_url") or "",
                    "parent_id": row.get("parent_id"),
                    "metadata": row.get("metadata") or {"source": "json"},
                }
            )
        return comments

