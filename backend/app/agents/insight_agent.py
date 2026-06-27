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
                "summary": "LLM 洞察未启用；本次仅输出规则分析、聚类结果和策略卡片。",
                "positive_insights": [],
                "negative_insights": [],
                "platform_differences": [],
                "risks": [],
                "recommendations": ["如需生成自然语言洞察，请启用 LLM 并确认 provider 可用。"],
            }
        return self.llm_service.generate_insight(context)
