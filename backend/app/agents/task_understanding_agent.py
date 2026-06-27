from __future__ import annotations

from typing import Any


class TaskUnderstandingAgent:
    """Normalize user task input into a predictable workflow config."""

    def run(self, task: Any) -> dict[str, Any]:
        """Return normalized task configuration."""

        platforms = ["hupu"]
        keywords = [str(keyword).strip() for keyword in (task.keywords or []) if str(keyword).strip()]
        return {
            "task_id": task.id,
            "name": task.name,
            "domain": task.domain if task.domain in {"basketball", "football"} else "basketball",
            "platforms": platforms,
            "board": getattr(task, "board", "nba") or "nba",
            "match_name": getattr(task, "match_name", "") or "",
            "home_team": getattr(task, "home_team", "") or "",
            "away_team": getattr(task, "away_team", "") or "",
            "match_stage": getattr(task, "match_stage", "") or "",
            "match_date": getattr(task, "match_date", "") or "",
            "thread_urls": list(dict.fromkeys(getattr(task, "thread_urls", []) or [])),
            "news_urls": list(dict.fromkeys(getattr(task, "news_urls", []) or [])),
            "news_context": getattr(task, "news_context", "") or "",
            "keywords": keywords,
            "semantic_query": task.semantic_query or "评论洞察分析",
            "time_range": task.time_range or {},
            "max_comments": task.max_comments or 100,
            "similarity_threshold": task.similarity_threshold or 0.86,
            "language": task.language or "zh",
            "sentiment_focus": task.sentiment_focus or "all",
            "enable_llm": task.enable_llm,
            "enable_image_analysis": getattr(task, "enable_image_analysis", True),
            "max_image_comments": max(0, min(20, int(getattr(task, "max_image_comments", 6) or 0))),
            "data_source": getattr(task, "data_source", "mock") or "mock",
            "source_path": getattr(task, "source_path", None),
        }
