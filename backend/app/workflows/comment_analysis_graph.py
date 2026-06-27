from __future__ import annotations

import logging
import time
from collections import Counter, defaultdict
from typing import Any

from app.agents.cleaning_agent import DataCleaningAgent
from app.agents.clustering_agent import ClusteringAgent
from app.agents.crawler_agent import CommentCrawlerAgent
from app.agents.dedup_agent import DeduplicationAgent
from app.agents.insight_agent import InsightGenerationAgent
from app.agents.painpoint_agent import PainPointAgent
from app.agents.platform_router_agent import PlatformRouterAgent
from app.agents.positive_attribution_agent import PositiveAttributionAgent
from app.agents.sampler_agent import RepresentativeSamplerAgent
from app.agents.sentiment_agent import SentimentAgent
from app.agents.strategy_card_agent import StrategyCardAgent
from app.agents.task_understanding_agent import TaskUnderstandingAgent
from app.agents.visualization_agent import VisualizationAgent
from app.services.data_quality_service import DataQualityService
from app.taxonomies import classify_stance

logger = logging.getLogger(__name__)


class CommentAnalysisGraph:
    """LangGraph-compatible Multi-Agent workflow for comment analysis."""

    def __init__(self) -> None:
        self.task_understanding_agent = TaskUnderstandingAgent()
        self.platform_router_agent = PlatformRouterAgent()
        self.crawler_agent = CommentCrawlerAgent()
        self.cleaning_agent = DataCleaningAgent()
        self.dedup_agent = DeduplicationAgent()
        self.sentiment_agent = SentimentAgent()
        self.positive_agent = PositiveAttributionAgent()
        self.painpoint_agent = PainPointAgent()
        self.clustering_agent = ClusteringAgent()
        self.sampler_agent = RepresentativeSamplerAgent()
        self.insight_agent = InsightGenerationAgent()
        self.strategy_agent = StrategyCardAgent()
        self.visualization_agent = VisualizationAgent()
        self.data_quality_service = DataQualityService()

    def run(self, task: Any) -> dict[str, Any]:
        """Run the workflow, preferring LangGraph when it is available."""

        try:
            return self._run_langgraph(task)
        except Exception as exc:  # pragma: no cover - depends on optional LangGraph runtime
            logger.info("LangGraph runtime unavailable, using sequential workflow: %s", exc)
            return self._run_sequential({"task": task})

    def _run_langgraph(self, task: Any) -> dict[str, Any]:
        from langgraph.graph import END, StateGraph

        graph = StateGraph(dict)
        graph.add_node("understand", self._timed_node("understand", self._understand))
        graph.add_node("route", self._timed_node("route", self._route))
        graph.add_node("crawl", self._timed_node("crawl", self._crawl))
        graph.add_node("clean", self._timed_node("clean", self._clean))
        graph.add_node("dedup", self._timed_node("dedup", self._dedup))
        graph.add_node("quality", self._timed_node("quality", self._quality))
        graph.add_node("sentiment", self._timed_node("sentiment", self._sentiment))
        graph.add_node("attribute", self._timed_node("attribute", self._attribute))
        graph.add_node("cluster", self._timed_node("cluster", self._cluster))
        graph.add_node("sample", self._timed_node("sample", self._sample))
        graph.add_node("insight", self._timed_node("insight", self._insight))
        graph.add_node("strategy", self._timed_node("strategy", self._strategy))
        graph.add_node("visualize", self._timed_node("visualize", self._visualize))
        graph.set_entry_point("understand")
        graph.add_edge("understand", "route")
        graph.add_edge("route", "crawl")
        graph.add_edge("crawl", "clean")
        graph.add_edge("clean", "dedup")
        graph.add_edge("dedup", "quality")
        graph.add_edge("quality", "sentiment")
        graph.add_edge("sentiment", "attribute")
        graph.add_edge("attribute", "cluster")
        graph.add_edge("cluster", "sample")
        graph.add_edge("sample", "insight")
        graph.add_edge("insight", "strategy")
        graph.add_edge("strategy", "visualize")
        graph.add_edge("visualize", END)
        compiled = graph.compile()
        return compiled.invoke({"task": task})

    def _run_sequential(self, state: dict[str, Any]) -> dict[str, Any]:
        for name, node in [
            ("understand", self._understand),
            ("route", self._route),
            ("crawl", self._crawl),
            ("clean", self._clean),
            ("dedup", self._dedup),
            ("quality", self._quality),
            ("sentiment", self._sentiment),
            ("attribute", self._attribute),
            ("cluster", self._cluster),
            ("sample", self._sample),
            ("insight", self._insight),
            ("strategy", self._strategy),
            ("visualize", self._visualize),
        ]:
            state = self._run_step(name, node, state)
        return state

    def _timed_node(self, name: str, node: Any) -> Any:
        def wrapped(state: dict[str, Any]) -> dict[str, Any]:
            return self._run_step(name, node, state)

        return wrapped

    def _run_step(self, name: str, node: Any, state: dict[str, Any]) -> dict[str, Any]:
        progress = state.setdefault("agent_progress", {})
        input_summary = self._step_summary(name, state)
        progress[name] = {"status": "running", "duration_ms": None, "error": "", "input_summary": input_summary, "output_summary": ""}
        started_at = time.perf_counter()
        try:
            next_state = node(state)
        except Exception as exc:
            progress[name] = {
                "status": "error",
                "duration_ms": max(1, int((time.perf_counter() - started_at) * 1000)),
                "error": str(exc),
                "input_summary": input_summary,
                "output_summary": "",
            }
            raise
        progress[name] = {
            "status": "completed",
            "duration_ms": max(1, int((time.perf_counter() - started_at) * 1000)),
            "error": "",
            "input_summary": input_summary,
            "output_summary": self._step_summary(name, next_state),
        }
        next_state["agent_progress"] = progress
        return next_state

    def _step_summary(self, name: str, state: dict[str, Any]) -> str:
        raw_count = len(state.get("raw_comments", []))
        comment_count = len(state.get("comments", []))
        dedup_count = len([item for item in state.get("comments", []) if not item.get("is_duplicate")])
        cluster_count = len(state.get("clusters", []))
        card_count = len(state.get("strategy_cards", []))
        quality = state.get("data_quality_report") or {}
        if name in {"understand", "route"}:
            config = state.get("config", {})
            return f"domain={config.get('domain', '-')}, platforms={len(config.get('platforms', []))}, keywords={len(config.get('keywords', []))}"
        if name == "crawl":
            return f"raw_comments={raw_count}"
        if name in {"clean", "dedup", "sentiment", "attribute"}:
            return f"comments={comment_count}, deduped={dedup_count}"
        if name == "quality":
            return f"deduped={quality.get('dedup_count', dedup_count)}, confidence={quality.get('sample_confidence_level', '-')}"
        if name == "cluster":
            return f"clusters={cluster_count}, noise_ratio={quality.get('noise_ratio', '-')}"
        if name == "sample":
            return f"representatives={len(state.get('representatives', []))}"
        if name == "insight":
            return "insight=generated" if state.get("insight_report") else "insight=pending"
        if name == "strategy":
            return f"strategy_cards={card_count}"
        if name == "visualize":
            return f"charts={len(state.get('visualizations', {}))}, cards={card_count}"
        return f"raw={raw_count}, comments={comment_count}"

    def _understand(self, state: dict[str, Any]) -> dict[str, Any]:
        logger.info("TaskUnderstandingAgent started")
        state["config"] = self.task_understanding_agent.run(state["task"])
        return state

    def _route(self, state: dict[str, Any]) -> dict[str, Any]:
        logger.info("PlatformRouterAgent started")
        state.update(self.platform_router_agent.run(state["config"]))
        return state

    def _crawl(self, state: dict[str, Any]) -> dict[str, Any]:
        logger.info("CommentCrawlerAgent started")
        state["raw_comments"] = self.crawler_agent.run(state["connector_plans"])
        return state

    def _clean(self, state: dict[str, Any]) -> dict[str, Any]:
        logger.info("DataCleaningAgent started")
        state["comments"] = self.cleaning_agent.run(state["raw_comments"])
        return state

    def _dedup(self, state: dict[str, Any]) -> dict[str, Any]:
        logger.info("DeduplicationAgent started")
        threshold = state["config"].get("similarity_threshold", 0.92)
        state["comments"] = self.dedup_agent.run(state["comments"], threshold=threshold)
        return state

    def _quality(self, state: dict[str, Any]) -> dict[str, Any]:
        logger.info("DataQualityReport started")
        state["data_quality_report"] = self.data_quality_service.build(
            state.get("raw_comments", []), state.get("comments", [])
        )
        return state

    def _sentiment(self, state: dict[str, Any]) -> dict[str, Any]:
        logger.info("SentimentAgent started")
        state["comments"] = self.sentiment_agent.run(state["comments"])
        return state

    def _attribute(self, state: dict[str, Any]) -> dict[str, Any]:
        logger.info("PositiveAttributionAgent and PainPointAgent started")
        domain = state["config"].get("domain", "game")
        state["comments"] = self.positive_agent.run(state["comments"], domain=domain)
        state["comments"] = self.painpoint_agent.run(state["comments"], domain=domain)
        for comment in state["comments"]:
            stance, term, confidence = classify_stance(comment.get("cleaned_content", ""), domain)
            comment["stance"] = {"label": stance, "confidence": confidence, "reason": f"命中领域词：{term}" if term else ""}
        state["positive_attributions"] = _aggregate(state["comments"], "positive_attribution")
        state["painpoints"] = _aggregate(state["comments"], "painpoint")
        return state

    def _cluster(self, state: dict[str, Any]) -> dict[str, Any]:
        logger.info("ClusteringAgent started")
        domain = state["config"].get("domain", "game")
        state["clusters"] = self.clustering_agent.run(state["comments"], method="auto", domain=domain)
        quality = state.get("data_quality_report") or {}
        deduped = [comment for comment in state.get("comments", []) if not comment.get("is_duplicate")]
        noise_count = len([comment for comment in deduped if comment.get("cluster_id") == -1])
        if deduped:
            quality["noise_ratio"] = round(noise_count / len(deduped), 4)
            state["data_quality_report"] = quality
        return state

    def _sample(self, state: dict[str, Any]) -> dict[str, Any]:
        logger.info("RepresentativeSamplerAgent started")
        state["representatives"] = self.sampler_agent.run(state["comments"], state["clusters"])
        return state

    def _insight(self, state: dict[str, Any]) -> dict[str, Any]:
        logger.info("InsightGenerationAgent started")
        state["insight_report"] = self.insight_agent.run(state)
        return state

    def _strategy(self, state: dict[str, Any]) -> dict[str, Any]:
        logger.info("StrategyCardAgent started")
        state["strategy_cards"] = self.strategy_agent.run(state)
        return state

    def _visualize(self, state: dict[str, Any]) -> dict[str, Any]:
        logger.info("VisualizationAgent started")
        state["visualizations"] = self.visualization_agent.run(state)
        state["summary"] = {
            "raw_count": len(state.get("raw_comments", [])),
            "cleaned_count": len(state.get("comments", [])),
            "deduped_count": len([item for item in state.get("comments", []) if not item.get("is_duplicate")]),
            "sample_confidence_level": state.get("data_quality_report", {}).get("sample_confidence_level", "low"),
            "cluster_count": len(state.get("clusters", [])),
            "strategy_card_count": len(state.get("strategy_cards", [])),
        }
        return state


def _aggregate(comments: list[dict], field: str) -> list[dict[str, Any]]:
    non_duplicate = [comment for comment in comments if not comment.get("is_duplicate")]
    total = max(1, len(non_duplicate))
    grouped: dict[str, list[dict]] = defaultdict(list)
    for comment in non_duplicate:
        result = comment.get(field)
        if result:
            grouped[result["category"]].append(comment)
    rows: list[dict[str, Any]] = []
    for category, group in grouped.items():
        rows.append(
            {
                "category": category,
                "count": len(group),
                "ratio": round(len(group) / total, 4),
                "examples": [item["cleaned_content"] for item in sorted(group, key=lambda row: row.get("like_count", 0), reverse=True)[:3]],
                "sentiment_distribution": dict(Counter(item.get("sentiment", {}).get("label", "neutral") for item in group)),
            }
        )
    return sorted(rows, key=lambda row: row["count"], reverse=True)
