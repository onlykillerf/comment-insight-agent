from __future__ import annotations

from typing import Any


class TaskUnderstandingAgent:
    """Normalize user task input into a predictable workflow config."""

    def run(self, task: Any) -> dict[str, Any]:
        """Return normalized task configuration."""

        platforms = list(dict.fromkeys(task.platforms or ["hupu", "weibo", "zhihu"]))
        keywords = [str(keyword).strip() for keyword in (task.keywords or []) if str(keyword).strip()]
        return {
            "task_id": task.id,
            "name": task.name,
            "domain": task.domain or "game",
            "platforms": platforms,
            "keywords": keywords,
            "semantic_query": task.semantic_query or "评论洞察分析",
            "time_range": task.time_range or {},
            "max_comments": task.max_comments or 100,
            "similarity_threshold": task.similarity_threshold or 0.86,
            "language": task.language or "zh",
            "sentiment_focus": task.sentiment_focus or "all",
            "enable_llm": task.enable_llm,
            "data_source": getattr(task, "data_source", "mock") or "mock",
            "source_path": getattr(task, "source_path", None),
        }

