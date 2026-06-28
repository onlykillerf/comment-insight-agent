from __future__ import annotations

import csv
import io
import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.config import PROJECT_ROOT, get_settings
from app.models import UploadedDataset


CANONICAL_FIELDS = [
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
]

FIELD_ALIASES = {
    "id": ["id", "comment_id", "commentId", "cid"],
    "platform": ["platform", "source_platform"],
    "topic": ["topic", "title", "note_title"],
    "content": ["content", "comment", "comment_text", "review_text", "text", "content_text"],
    "author_hash": ["author_hash", "user_hash", "user_id", "author_id", "nickname"],
    "like_count": ["like_count", "likes", "like", "liked_count", "digg_count"],
    "reply_count": ["reply_count", "replies", "sub_comment_count"],
    "publish_time": ["publish_time", "created_at", "create_time", "review_time", "time"],
    "source_url": ["source_url", "url", "note_url", "detail_url"],
    "parent_id": ["parent_id", "parent_comment_id", "root_comment_id"],
}


class UploadService:
    """Persist, inspect, and map browser-uploaded comment datasets."""

    def __init__(self) -> None:
        self.settings = get_settings()

    async def create(self, db: Session, file: UploadFile, source_kind: str) -> UploadedDataset:
        if source_kind not in {"csv", "json", "mediacrawler"}:
            raise HTTPException(status_code=400, detail="上传类型必须是 CSV、JSON 或 MediaCrawler Export")
        original_name = Path(file.filename or "upload").name
        suffix = Path(original_name).suffix.lower()
        if suffix not in {".csv", ".json", ".jsonl"}:
            raise HTTPException(status_code=400, detail="仅支持 .csv、.json 和 .jsonl 文件")
        content = await file.read()
        max_bytes = self.settings.max_upload_mb * 1024 * 1024
        if not content:
            raise HTTPException(status_code=400, detail="上传文件为空")
        if len(content) > max_bytes:
            raise HTTPException(status_code=413, detail=f"文件不能超过 {self.settings.max_upload_mb} MB")

        upload_id = str(uuid4())
        upload_dir = Path(self.settings.upload_dir)
        if not upload_dir.is_absolute():
            upload_dir = PROJECT_ROOT / upload_dir
        upload_dir.mkdir(parents=True, exist_ok=True)
        stored_path = upload_dir / f"{upload_id}{suffix}"
        stored_path.write_bytes(content)
        try:
            rows = self.read_rows(stored_path)
        except (UnicodeDecodeError, csv.Error, json.JSONDecodeError, ValueError) as exc:
            stored_path.unlink(missing_ok=True)
            raise HTTPException(status_code=400, detail=f"文件解析失败：{exc}") from exc
        if not rows:
            stored_path.unlink(missing_ok=True)
            raise HTTPException(status_code=400, detail="文件中没有可读取的数据行")

        columns = list(dict.fromkeys(key for row in rows for key in row.keys()))
        mapping = self.auto_mapping(columns)
        errors = self.mapping_errors(mapping, columns)
        dataset = UploadedDataset(
            id=upload_id,
            original_name=original_name,
            stored_path=str(stored_path),
            source_kind=source_kind,
            file_format=suffix.lstrip("."),
            size_bytes=len(content),
            row_count=len(rows),
            columns=columns,
            preview_rows=rows[:10],
            field_mapping=mapping,
            validation_errors=errors,
            status="ready" if not errors else "needs_mapping",
        )
        db.add(dataset)
        db.commit()
        db.refresh(dataset)
        return dataset

    def update_mapping(self, db: Session, dataset: UploadedDataset, mapping: dict[str, str]) -> UploadedDataset:
        cleaned = {
            canonical: source
            for canonical, source in mapping.items()
            if canonical in CANONICAL_FIELDS and source
        }
        errors = self.mapping_errors(cleaned, dataset.columns)
        dataset.field_mapping = cleaned
        dataset.validation_errors = errors
        dataset.status = "ready" if not errors else "needs_mapping"
        db.commit()
        db.refresh(dataset)
        return dataset

    @staticmethod
    def read_rows(path: Path) -> list[dict[str, Any]]:
        suffix = path.suffix.lower()
        text = path.read_text(encoding="utf-8-sig")
        if suffix == ".csv":
            return [dict(row) for row in csv.DictReader(io.StringIO(text))]
        if suffix == ".jsonl":
            return [json.loads(line) for line in text.splitlines() if line.strip()]
        payload = json.loads(text)
        if isinstance(payload, list):
            rows = payload
        elif isinstance(payload, dict):
            rows = next(
                (payload[key] for key in ["comments", "data", "items", "records"] if isinstance(payload.get(key), list)),
                [],
            )
        else:
            rows = []
        if any(not isinstance(row, dict) for row in rows):
            raise ValueError("JSON 数据行必须是 object")
        return [dict(row) for row in rows]

    @staticmethod
    def auto_mapping(columns: list[str]) -> dict[str, str]:
        lookup = {column.lower(): column for column in columns}
        mapping: dict[str, str] = {}
        for canonical, aliases in FIELD_ALIASES.items():
            source = next((lookup[alias.lower()] for alias in aliases if alias.lower() in lookup), None)
            if source:
                mapping[canonical] = source
        return mapping

    @staticmethod
    def mapping_errors(mapping: dict[str, str], columns: list[str]) -> list[str]:
        errors: list[str] = []
        if not mapping.get("content"):
            errors.append("请选择评论正文对应字段")
        invalid = [source for source in mapping.values() if source not in columns]
        if invalid:
            errors.append(f"映射字段不存在：{', '.join(invalid)}")
        return errors
