from __future__ import annotations

import json
from pathlib import Path

from app.connectors.base import FetchRequest, NormalizedComment
from app.connectors.csv_connector import normalize_row


class JsonConnector:
    """Connector for user-provided JSON sample files."""

    name = "json"

    def fetch_comments(self, request: FetchRequest) -> list[NormalizedComment]:
        """Read normalized comments from a JSON list or object with comments."""

        if not request.source_path:
            raise ValueError("JsonConnector requires source_path")
        path = Path(request.source_path)
        text = path.read_text(encoding="utf-8-sig")
        if path.suffix.lower() == ".jsonl":
            rows = [json.loads(line) for line in text.splitlines() if line.strip()]
        else:
            payload = json.loads(text)
            rows = (
                next(
                    (payload[key] for key in ["comments", "data", "items", "records"] if isinstance(payload.get(key), list)),
                    [],
                )
                if isinstance(payload, dict)
                else payload
            )
        comments: list[NormalizedComment] = []
        for row in rows[: request.max_comments]:
            comments.append(normalize_row(row, request.platform, request.semantic_query, request.field_mapping))
        return comments
