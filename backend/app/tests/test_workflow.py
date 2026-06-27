from __future__ import annotations

from app.models import Task
from app.workflows.comment_analysis_graph import CommentAnalysisGraph


def test_workflow_generates_complete_demo_result() -> None:
    task = Task(
        id=1,
        name="pytest demo",
        domain="basketball",
        platforms=["hupu"],
        board="nba",
        match_name="马刺 vs 尼克斯 G6",
        home_team="马刺",
        away_team="尼克斯",
        match_stage="总决赛 G6",
        match_date="2026-06-20",
        thread_urls=[],
        news_urls=[],
        news_context="马刺在系列赛中暂时 3-2 领先，本场为第六场。",
        keywords=["马刺", "尼克斯", "G6"],
        semantic_query="分析虎扑网友对马刺和尼克斯 G6 的看法",
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

    assert result["summary"]["raw_count"] >= 12
    assert result["summary"]["deduped_count"] >= 6
    assert result["summary"]["news_context_count"] == 1
    assert result["insight_report"]["summary"]
    assert result["insight_report"]["fact_opinion_gaps"]
    assert "strategy_cards" not in result
    assert "strategy" not in result["agent_progress"]
    assert result["clusters"]
