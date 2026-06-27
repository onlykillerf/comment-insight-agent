from __future__ import annotations

import csv
import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from app.connectors.base import FetchRequest, NormalizedComment

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class MediaCrawlerExportConnector:
    """Import comments exported by NanmiCoder/MediaCrawler.

    This connector intentionally does not drive browser automation, login,
    proxy pools, or request signing. It only normalizes exported files that the
    user has already collected lawfully and wants to analyze.
    """

    name = "mediacrawler"

    platform_aliases = {
        "xhs": "xhs",
        "xiaohongshu": "xhs",
        "小红书": "xhs",
        "dy": "dy",
        "douyin": "dy",
        "抖音": "dy",
        "ks": "ks",
        "kuaishou": "ks",
        "快手": "ks",
        "bili": "bili",
        "bilibili": "bili",
        "b站": "bili",
        "wb": "wb",
        "weibo": "wb",
        "微博": "wb",
        "tieba": "tieba",
        "贴吧": "tieba",
        "zhihu": "zhihu",
        "知乎": "zhihu",
    }

    table_platforms = {
        "xhs_note_comment": "xhs",
        "douyin_aweme_comment": "dy",
        "kuaishou_video_comment": "ks",
        "bilibili_video_comment": "bili",
        "weibo_note_comment": "wb",
        "tieba_comment": "tieba",
        "zhihu_comment": "zhihu",
    }

    comment_table_names = set(table_platforms)
    supported_suffixes = {".csv", ".json", ".jsonl", ".db", ".sqlite", ".sqlite3"}

    def fetch_comments(self, request: FetchRequest) -> list[NormalizedComment]:
        """Read MediaCrawler export files and return normalized comments."""

        if not request.source_path:
            raise ValueError("MediaCrawlerExportConnector requires source_path")
        source = self._resolve_source_path(request.source_path)
        if not source.exists():
            raise FileNotFoundError(f"MediaCrawler export path does not exist: {source}")

        target_platform = self._canonical_platform(request.platform)
        comments: list[NormalizedComment] = []
        for record in self._iter_records(source):
            platform = self._infer_platform(record, target_platform)
            if target_platform and platform != target_platform:
                continue
            normalized = self._normalize(record, platform, request)
            if normalized["content"]:
                comments.append(normalized)
            if len(comments) >= request.max_comments:
                break
        return comments

    def _resolve_source_path(self, source_path: str) -> Path:
        source = Path(source_path)
        if source.exists():
            return source
        if not source.is_absolute():
            project_source = PROJECT_ROOT / source
            if project_source.exists():
                return project_source
        return source

    def _iter_records(self, source: Path) -> Iterable[dict[str, Any]]:
        files = [source] if source.is_file() else self._discover_files(source)
        for path in files:
            suffix = path.suffix.lower()
            if suffix == ".csv":
                yield from self._read_csv(path)
            elif suffix == ".json":
                yield from self._read_json(path)
            elif suffix == ".jsonl":
                yield from self._read_jsonl(path)
            elif suffix in {".db", ".sqlite", ".sqlite3"}:
                yield from self._read_sqlite(path)

    def _discover_files(self, root: Path) -> list[Path]:
        candidates: list[Path] = []
        for path in root.rglob("*"):
            if path.is_dir() or path.suffix.lower() not in self.supported_suffixes:
                continue
            lowered = path.name.lower()
            if "comment" in lowered or any(table in lowered for table in self.comment_table_names):
                candidates.append(path)
        return sorted(candidates)

    def _read_csv(self, path: Path) -> Iterable[dict[str, Any]]:
        with path.open("r", encoding="utf-8-sig", newline="") as file:
            for row in csv.DictReader(file):
                yield self._with_source(row, path, self._infer_table_from_name(path.name))

    def _read_json(self, path: Path) -> Iterable[dict[str, Any]]:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            rows = payload
        elif isinstance(payload, dict):
            rows = payload.get("comments") or payload.get("data") or payload.get("items") or []
            if not rows:
                for table, value in payload.items():
                    if table in self.comment_table_names and isinstance(value, list):
                        for item in value:
                            yield self._with_source(item, path, table)
                return
        else:
            rows = []
        for row in rows:
            if isinstance(row, dict):
                yield self._with_source(row, path, self._infer_table_from_name(path.name))

    def _read_jsonl(self, path: Path) -> Iterable[dict[str, Any]]:
        table = self._infer_table_from_name(path.name)
        with path.open("r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                if isinstance(row, dict):
                    yield self._with_source(row, path, table)

    def _read_sqlite(self, path: Path) -> Iterable[dict[str, Any]]:
        connection = sqlite3.connect(path)
        connection.row_factory = sqlite3.Row
        try:
            tables = [
                row["name"]
                for row in connection.execute("select name from sqlite_master where type='table'")
                if row["name"] in self.comment_table_names
            ]
            for table in tables:
                for row in connection.execute(f"select * from {table}"):
                    yield self._with_source(dict(row), path, table)
        finally:
            connection.close()

    def _with_source(self, row: dict[str, Any], path: Path, table: str | None) -> dict[str, Any]:
        item = dict(row)
        item["_source_file"] = str(path)
        if table:
            item["_source_table"] = table
        return item

    def _normalize(self, record: dict[str, Any], platform: str, request: FetchRequest) -> NormalizedComment:
        content = self._first(record, ["content", "content_text", "text", "comment", "comment_content"])
        source_id = self._first(
            record,
            ["note_id", "video_id", "aweme_id", "content_id", "dynamic_id", "tieba_id", "source_id"],
        )
        comment_id = self._first(record, ["comment_id", "id", "rpid", "cid"])
        author_raw = self._first(record, ["user_id", "sec_uid", "user_unique_id", "user_link", "nickname"])
        like_count = self._to_int(self._first(record, ["like_count", "comment_like_count", "liked_count", "voteup_count"]))
        reply_count = self._to_int(self._first(record, ["sub_comment_count", "comment_count", "comments_count"]))
        publish_time = self._normalize_time(self._first(record, ["create_date_time", "publish_time", "created_time", "create_time", "time"]))
        source_url = self._first(record, ["note_url", "aweme_url", "video_url", "content_url", "source_url"])
        parent_id = self._first(record, ["parent_comment_id", "root_comment_id", "parent_id"])
        note_title = self._first(record, ["note_title", "title", "note_display_title"])
        note_desc = self._first(record, ["note_desc", "desc", "note_content", "description"])
        source_query = self._first(record, ["source_query", "keyword", "query"])
        topic = self._first(record, ["source_keyword", "semantic_query", "note_id", "video_id", "aweme_id", "content_id"])
        topic = topic or note_title or note_desc or request.semantic_query
        stable_id = self._stable_comment_id(platform, source_id, comment_id, content)

        return {
            "id": stable_id,
            "platform": platform,
            "topic": str(topic or ""),
            "content": str(content or ""),
            "author_hash": self._hash_author(author_raw),
            "like_count": like_count,
            "reply_count": reply_count,
            "publish_time": publish_time,
            "source_url": str(source_url or ""),
            "parent_id": str(parent_id) if parent_id else None,
            "metadata": {
                "source": "mediacrawler_export",
                "source_file": record.get("_source_file", ""),
                "source_table": record.get("_source_table", ""),
                "source_keyword": record.get("source_keyword", ""),
                "source_query": source_query or "",
                "source_id": source_id or "",
                "note_title": note_title or "",
                "note_desc": note_desc or "",
                "note_media_type": record.get("note_media_type", ""),
                "note_image_count": self._to_int(record.get("note_image_count", 0)),
                "note_video_count": self._to_int(record.get("note_video_count", 0)),
                "note_media_hints": record.get("note_media_hints", []),
            },
        }

    def _infer_platform(self, record: dict[str, Any], fallback: str) -> str:
        explicit = self._canonical_platform(str(record.get("platform") or ""))
        if explicit:
            return explicit
        table = str(record.get("_source_table") or "")
        if table in self.table_platforms:
            return self.table_platforms[table]
        source_file = Path(str(record.get("_source_file") or "")).name
        table_from_name = self._infer_table_from_name(source_file)
        if table_from_name and table_from_name in self.table_platforms:
            return self.table_platforms[table_from_name]
        for alias, platform in self.platform_aliases.items():
            if alias and alias in source_file.lower():
                return platform
        return fallback

    def _infer_table_from_name(self, filename: str) -> str | None:
        lowered = filename.lower()
        for table in self.comment_table_names:
            if table in lowered:
                return table
        return None

    def _canonical_platform(self, platform: str) -> str:
        return self.platform_aliases.get(platform.strip().lower(), platform.strip().lower())

    def _first(self, record: dict[str, Any], keys: list[str]) -> Any:
        for key in keys:
            value = record.get(key)
            if value not in (None, ""):
                return value
        return ""

    def _to_int(self, value: Any) -> int:
        try:
            return int(float(str(value).replace(",", "")))
        except (TypeError, ValueError):
            return 0

    def _normalize_time(self, value: Any) -> str:
        if value in (None, ""):
            return ""
        text = str(value)
        if text.isdigit():
            timestamp = int(text)
            if timestamp > 10_000_000_000:
                timestamp = timestamp // 1000
            return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()
        return text

    def _stable_comment_id(self, platform: str, source_id: Any, comment_id: Any, content: Any) -> str:
        if comment_id:
            return f"mediacrawler-{platform}-{comment_id}"
        digest = hashlib.sha1(f"{platform}:{source_id}:{content}".encode("utf-8")).hexdigest()[:16]
        return f"mediacrawler-{platform}-{digest}"

    def _hash_author(self, value: Any) -> str:
        if value in (None, ""):
            return ""
        return hashlib.sha1(str(value).encode("utf-8")).hexdigest()[:16]
