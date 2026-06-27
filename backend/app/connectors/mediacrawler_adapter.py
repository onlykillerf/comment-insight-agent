from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any

from app.config import get_settings
from app.connectors.base import FetchRequest, NormalizedComment
from app.connectors.mediacrawler_export_connector import MediaCrawlerExportConnector


class MediaCrawlerAdapter:
    """Thin adapter around a local NanmiCoder/MediaCrawler checkout.

    The adapter does not vendor or reimplement MediaCrawler. It can launch a
    local checkout when explicitly configured, then normalizes exported files
    through MediaCrawlerExportConnector.
    """

    name = "mediacrawler_adapter"
    supported_platforms = {"xhs", "dy", "ks", "bili", "wb", "tieba", "zhihu"}

    def __init__(self, media_crawler_path: str | None = None) -> None:
        settings = get_settings()
        configured_path = media_crawler_path or os.getenv("MEDIA_CRAWLER_PATH") or settings.media_crawler_path
        self.media_crawler_path = Path(configured_path).expanduser() if configured_path else None
        self.export_connector = MediaCrawlerExportConnector()

    def is_available(self) -> bool:
        """Return whether a local MediaCrawler checkout is configured."""

        return bool(self.media_crawler_path and self.media_crawler_path.exists())

    def fetch_comments(self, request: FetchRequest) -> list[NormalizedComment]:
        """Read an existing export file, or run MediaCrawler when explicitly configured."""

        if request.source_path:
            return self.export_connector.fetch_comments(request)
        output_path = self.run_mediacrawler(request)
        export_request = FetchRequest(
            task_id=request.task_id,
            platform=request.platform,
            domain=request.domain,
            keywords=request.keywords,
            semantic_query=request.semantic_query,
            time_range=request.time_range,
            max_comments=request.max_comments,
            source_path=str(output_path),
        )
        return self.export_connector.fetch_comments(export_request)

    def run_mediacrawler(self, request: FetchRequest, extra_args: list[str] | None = None) -> Path:
        """Call a local MediaCrawler checkout and return its output directory."""

        if not self.is_available():
            raise RuntimeError("MEDIA_CRAWLER_PATH is not configured or does not exist")
        platform = self.export_connector._canonical_platform(request.platform)
        if platform not in self.supported_platforms:
            raise ValueError(f"MediaCrawlerAdapter does not support platform: {request.platform}")

        output_dir = Path("data") / "mediacrawler_outputs" / f"task_{request.task_id}_{platform}"
        output_dir.mkdir(parents=True, exist_ok=True)
        keyword = request.keywords[0] if request.keywords else request.semantic_query
        command = [
            "python",
            "main.py",
            "--platform",
            platform,
            "--keywords",
            keyword,
            "--save_data_option",
            "json",
            "--output",
            str(output_dir),
        ]
        command.extend(extra_args or [])
        subprocess.run(command, cwd=self.media_crawler_path, check=True)
        return output_dir

    def convert_output(self, source_path: str, request: FetchRequest) -> list[NormalizedComment]:
        """Normalize MediaCrawler CSV/JSON/JSONL/SQLite output to RawComment schema."""

        export_request = FetchRequest(
            task_id=request.task_id,
            platform=request.platform,
            domain=request.domain,
            keywords=request.keywords,
            semantic_query=request.semantic_query,
            time_range=request.time_range,
            max_comments=request.max_comments,
            source_path=source_path,
        )
        return self.export_connector.fetch_comments(export_request)

    def output_schema_hint(self) -> dict[str, Any]:
        """Document the normalized RawComment fields produced by the adapter."""

        return {
            "platforms": sorted(self.supported_platforms),
            "raw_comment_fields": [
                "id",
                "platform",
                "topic",
                "content",
                "author_hash",
                "like_count",
                "reply_count",
                "publish_time",
                "source_url",
                "parent_id",
                "metadata",
            ],
        }
