from __future__ import annotations

import json

from app.agents.strategy_card_agent import StrategyCardAgent
from app.connectors.base import FetchRequest
from app.connectors.mediacrawler_adapter import MediaCrawlerAdapter
from app.services.data_quality_service import SMALL_SAMPLE_WARNING, DataQualityService
from app.taxonomies import classify_label, get_taxonomy


def test_data_quality_report_counts_are_correct() -> None:
    raw_comments = [{"id": str(index)} for index in range(5)]
    comments = [
        {"id": "1", "language": "zh", "is_duplicate": False},
        {"id": "2", "language": "zh", "is_duplicate": False},
        {"id": "3", "language": "en", "is_duplicate": True},
        {"id": "4", "language": "zh", "is_duplicate": False},
    ]

    report = DataQualityService().build(raw_comments, comments)

    assert report["raw_count"] == 5
    assert report["clean_count"] == 4
    assert report["dedup_count"] == 3
    assert report["duplicate_ratio"] == 0.25
    assert report["noise_ratio"] == 0.2
    assert report["language_distribution"] == {"zh": 3, "en": 1}


def test_small_sample_warning_is_present() -> None:
    report = DataQualityService().build([{"id": "1"}], [{"id": "1", "language": "zh", "is_duplicate": False}])

    assert report["sample_confidence_level"] == "low"
    assert report["warning"] == SMALL_SAMPLE_WARNING


def test_strategy_affected_ratio_uses_real_count() -> None:
    cards = StrategyCardAgent().run(
        {
            "config": {"domain": "nba_draft"},
            "data_quality_report": {"dedup_count": 20},
            "painpoints": [
                {
                    "category": "顺位过高争议",
                    "count": 4,
                    "ratio": 0.99,
                    "examples": ["这个顺位过高，不值。", "前十选他太冒险。"],
                }
            ],
            "positive_attributions": [],
            "comments": [],
        }
    )

    assert cards
    assert cards[0]["affected_ratio"] == "20.0%"
    assert cards[0]["evidence_count"] == 4
    assert cards[0]["sample_size"] == 20
    assert "顺位" in " ".join(cards[0]["suggested_actions"])


def test_mediacrawler_adapter_converts_mock_output(tmp_path) -> None:
    export_path = tmp_path / "xhs_note_comment.jsonl"
    export_path.write_text(
        json.dumps(
            {
                "comment_id": "c1",
                "note_id": "n1",
                "platform": "xhs",
                "content": "这届选秀这个锋线身体模板很好，挺看好。",
                "nickname": "tester",
                "like_count": 8,
                "create_time": "1719388800",
                "note_title": "2026 NBA 选秀观察",
                "note_desc": "拆解热门新秀模板和球队适配。",
                "note_media_type": "image",
                "note_image_count": 3,
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    comments = MediaCrawlerAdapter().convert_output(
        str(export_path),
        FetchRequest(
            task_id=1,
            platform="xhs",
            domain="nba_draft",
            keywords=["2026 NBA 选秀"],
            semantic_query="分析 2026 NBA 选秀评论",
            max_comments=10,
        ),
    )

    assert len(comments) == 1
    assert comments[0]["platform"] == "xhs"
    assert comments[0]["content"] == "这届选秀这个锋线身体模板很好，挺看好。"
    assert comments[0]["metadata"]["note_title"] == "2026 NBA 选秀观察"
    assert comments[0]["metadata"]["note_image_count"] == 3


def test_nba_draft_taxonomy_classifies_labels() -> None:
    taxonomy = get_taxonomy("nba_draft")

    assert "天赋与身体模板" in taxonomy.positive_labels
    assert "顺位过高争议" in taxonomy.negative_labels
    assert "看好" in taxonomy.stance_labels
    assert classify_label("这个新秀身体模板好，成长空间也大", "nba_draft", "positive")[0] == "天赋与身体模板"
    assert classify_label("前十选他顺位过高，不值", "nba_draft", "negative")[0] == "顺位过高争议"
