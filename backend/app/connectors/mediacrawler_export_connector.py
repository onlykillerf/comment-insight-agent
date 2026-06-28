from __future__ import annotations

from pathlib import Path

from app.connectors.base import FetchRequest, NormalizedComment
from app.connectors.csv_connector import CSVConnector
from app.connectors.json_connector import JsonConnector


class MediaCrawlerExportConnector:
    """Read user-uploaded MediaCrawler CSV, JSON, or JSONL exports."""

    name = "mediacrawler"

    def fetch_comments(self, request: FetchRequest) -> list[NormalizedComment]:
        if not request.source_path:
            raise ValueError("MediaCrawler Export 需要先上传文件")
        suffix = Path(request.source_path).suffix.lower()
        if suffix == ".csv":
            return CSVConnector().fetch_comments(request)
        if suffix in {".json", ".jsonl"}:
            return JsonConnector().fetch_comments(request)
        raise ValueError(f"不支持的 MediaCrawler Export 格式：{suffix}")
