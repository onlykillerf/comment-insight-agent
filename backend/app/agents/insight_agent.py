from __future__ import annotations

from typing import Any

from app.services.llm_service import LLMService


class InsightGenerationAgent:
    """Generate structured insights through the configured LLM service."""

    def __init__(self, llm_service: LLMService | None = None) -> None:
        self.llm_service = llm_service or LLMService()

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        """Return a structured insight report."""

        if not context.get("config", {}).get("enable_llm", True):
            return {
                "summary": "LLM 洞察未启用；本次仅输出规则分析、聚类结果和典型评论。",
                "positive_insights": [],
                "negative_insights": [],
                "key_viewpoints": [],
                "controversies": [],
                "news_context_summary": "",
                "context_alignment": [],
                "fact_opinion_gaps": [],
                "risks": [],
            }
        return self.llm_service.generate_insight(context)
