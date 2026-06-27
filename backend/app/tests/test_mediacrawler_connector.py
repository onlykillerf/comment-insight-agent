from __future__ import annotations

import json

from app.connectors.base import FetchRequest
from app.connectors.mediacrawler_export_connector import MediaCrawlerExportConnector


def test_mediacrawler_jsonl_export_normalizes_comment(tmp_path) -> None:
    export_path = tmp_path / "weibo_note_comment.jsonl"
    export_path.write_text(
        json.dumps(
            {
                "comment_id": "1001",
                "note_id": "2001",
                "content": "广告太频繁，刚进入关键环节就弹窗。",
                "user_id": "user-1",
                "comment_like_count": "12",
                "sub_comment_count": "3",
                "create_time": "1719388800",
                "parent_comment_id": "",
                "source_keyword": "广告体验",
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    comments = MediaCrawlerExportConnector().fetch_comments(
        FetchRequest(
            task_id=1,
            platform="weibo",
            domain="game",
            keywords=["广告"],
            semantic_query="广告体验",
            max_comments=10,
            source_path=str(export_path),
        )
    )

    assert len(comments) == 1
    assert comments[0]["platform"] == "wb"
    assert comments[0]["content"] == "广告太频繁，刚进入关键环节就弹窗。"
    assert comments[0]["like_count"] == 12
    assert comments[0]["reply_count"] == 3
    assert comments[0]["metadata"]["source"] == "mediacrawler_export"

