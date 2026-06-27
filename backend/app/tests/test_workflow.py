from __future__ import annotations

from app.models import Task
from app.workflows.comment_analysis_graph import CommentAnalysisGraph


def test_workflow_generates_complete_demo_result() -> None:
    task = Task(
        id=1,
        name="pytest demo",
        domain="game",
        platforms=["weibo", "zhihu", "hupu"],
        keywords=["广告", "卡顿", "爽"],
        semantic_query="测试评论闭环",
        time_range={},
        max_comments=30,
        similarity_threshold=0.92,
        language="zh",
        sentiment_focus="all",
        enable_llm=True,
        data_source="mock",
        progress={},
    )

    result = CommentAnalysisGraph().run(task)

    assert result["summary"]["raw_count"] >= 9
    assert result["summary"]["deduped_count"] >= 6
    assert result["insight_report"]["summary"]
    assert result["strategy_cards"]
    assert all(len(card["evidence_comments"]) >= 2 for card in result["strategy_cards"])
    assert all(card["affected_ratio"].endswith("%") for card in result["strategy_cards"])
    assert result["clusters"]
