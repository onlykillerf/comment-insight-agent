from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models import (
    ABTestDraft,
    CleanComment,
    ClusterResult,
    CommentEmbedding,
    DataQualityReport,
    InsightReport,
    PainPointResult,
    PositiveAttributionResult,
    RawComment,
    RepresentativeComment,
    SentimentResult,
    StrategyCard,
    Task,
)
from app.services.strategy_card_service import StrategyCardService
from app.services.exceptions import TaskCancelledError
from app.workflows.comment_analysis_graph import CommentAnalysisGraph


AGENT_STEPS = [
    "understand",
    "route",
    "crawl",
    "context",
    "media",
    "clean",
    "dedup",
    "quality",
    "sentiment",
    "attribute",
    "cluster",
    "sample",
    "insight",
    "visualize",
]


def initial_progress() -> dict[str, dict[str, Any]]:
    return {
        key: {
            "status": "pending",
            "duration_ms": None,
            "error": "",
            "input_summary": "",
            "output_summary": "",
        }
        for key in AGENT_STEPS
    }


def run_and_store_task(
    db: Session,
    task: Task,
    progress_callback: Any | None = None,
    cancel_check: Any | None = None,
) -> dict[str, Any]:
    """Run the full workflow and persist analysis artifacts."""

    _clear_task_results(db, task.id)
    task.status = "running"
    task.error_message = ""
    if cancel_check is None:
        task.cancel_requested = False
    task.started_at = task.started_at or datetime.now(timezone.utc)
    task.finished_at = None
    task.progress = initial_progress()
    db.commit()
    if progress_callback:
        progress_callback(task.progress)

    try:
        result = CommentAnalysisGraph(
            progress_callback=progress_callback,
            cancel_check=cancel_check,
        ).run(task)
        if cancel_check and cancel_check():
            raise TaskCancelledError("任务已由用户取消")
        _store_result(db, task, result)
        task.status = "completed"
        task.error_message = ""
        task.finished_at = datetime.now(timezone.utc)
        task.progress = result.get("agent_progress") or task.progress
        db.commit()
        db.refresh(task)
        return result.get("summary", {})
    except TaskCancelledError as exc:
        db.rollback()
        current = db.get(Task, task.id)
        if current:
            current.status = "cancelled"
            current.error_message = str(exc)
            current.finished_at = datetime.now(timezone.utc)
            current.cancel_requested = True
            db.commit()
        raise
    except Exception as exc:
        db.rollback()
        current = db.get(Task, task.id)
        if current:
            current.status = "failed"
            current.error_message = str(exc)[:2000]
            current.finished_at = datetime.now(timezone.utc)
            db.commit()
        raise


def _clear_task_results(db: Session, task_id: int) -> None:
    clean_ids = [row[0] for row in db.query(CleanComment.id).filter(CleanComment.task_id == task_id).all()]
    if clean_ids:
        db.query(SentimentResult).filter(SentimentResult.comment_id.in_(clean_ids)).delete(synchronize_session=False)
        db.query(PainPointResult).filter(PainPointResult.comment_id.in_(clean_ids)).delete(synchronize_session=False)
        db.query(PositiveAttributionResult).filter(
            PositiveAttributionResult.comment_id.in_(clean_ids)
        ).delete(synchronize_session=False)
        db.query(CommentEmbedding).filter(CommentEmbedding.comment_id.in_(clean_ids)).delete(synchronize_session=False)
    db.query(RepresentativeComment).filter(RepresentativeComment.task_id == task_id).delete(synchronize_session=False)
    db.query(ClusterResult).filter(ClusterResult.task_id == task_id).delete(synchronize_session=False)
    db.query(DataQualityReport).filter(DataQualityReport.task_id == task_id).delete(synchronize_session=False)
    db.query(InsightReport).filter(InsightReport.task_id == task_id).delete(synchronize_session=False)
    card_ids = [row[0] for row in db.query(StrategyCard.id).filter(StrategyCard.task_id == task_id).all()]
    if card_ids:
        db.query(ABTestDraft).filter(ABTestDraft.strategy_card_id.in_(card_ids)).delete(synchronize_session=False)
    db.query(StrategyCard).filter(StrategyCard.task_id == task_id).delete(synchronize_session=False)
    db.query(CleanComment).filter(CleanComment.task_id == task_id).delete(synchronize_session=False)
    db.query(RawComment).filter(RawComment.task_id == task_id).delete(synchronize_session=False)
    db.flush()


def _store_result(db: Session, task: Task, result: dict[str, Any]) -> None:
    raw_id_map: dict[str, str] = {}
    for comment in result.get("raw_comments", []):
        raw_id = f"{task.id}:{comment['id']}"
        raw_id_map[str(comment["id"])] = raw_id
        db.add(
            RawComment(
                id=raw_id,
                task_id=task.id,
                platform=comment.get("platform", ""),
                topic=comment.get("topic", ""),
                content=comment.get("content", ""),
                author_hash=comment.get("author_hash", ""),
                like_count=int(comment.get("like_count") or 0),
                reply_count=int(comment.get("reply_count") or 0),
                publish_time=comment.get("publish_time", ""),
                source_url=comment.get("source_url", ""),
                parent_id=comment.get("parent_id"),
                image_urls=comment.get("image_urls") or [],
                image_analysis=comment.get("image_analysis") or {},
                metadata_json=comment.get("metadata") or {},
            )
        )
    db.flush()

    clean_by_raw_id: dict[str, CleanComment] = {}
    for comment in result.get("comments", []):
        raw_id = raw_id_map.get(str(comment["id"]), f"{task.id}:{comment['id']}")
        clean = CleanComment(
            task_id=task.id,
            raw_comment_id=raw_id,
            content=comment.get("content", ""),
            cleaned_content=comment.get("cleaned_content", ""),
            language=comment.get("language", "zh"),
            quality_score=float(comment.get("quality_score") or 0),
            is_duplicate=bool(comment.get("is_duplicate")),
            duplicate_group_id=comment.get("duplicate_group_id"),
            cluster_id=comment.get("cluster_id"),
        )
        db.add(clean)
        db.flush()
        clean_by_raw_id[str(comment["id"])] = clean
        db.add(
            CommentEmbedding(
                comment_id=clean.id,
                vector_store_id=f"local:{clean.id}",
                embedding_model="hashing-embedding-v1",
                vector=comment.get("embedding") or [],
            )
        )
        if comment.get("sentiment"):
            db.add(SentimentResult(comment_id=clean.id, **comment["sentiment"]))
        if comment.get("painpoint"):
            db.add(PainPointResult(comment_id=clean.id, **comment["painpoint"]))
        if comment.get("positive_attribution"):
            db.add(PositiveAttributionResult(comment_id=clean.id, **comment["positive_attribution"]))

    quality = result.get("data_quality_report") or {}
    db.add(
        DataQualityReport(
            task_id=task.id,
            raw_count=int(quality.get("raw_count") or 0),
            clean_count=int(quality.get("clean_count") or 0),
            dedup_count=int(quality.get("dedup_count") or 0),
            duplicate_ratio=float(quality.get("duplicate_ratio") or 0),
            noise_ratio=float(quality.get("noise_ratio") or 0),
            language_distribution=quality.get("language_distribution") or {},
            sample_confidence_level=quality.get("sample_confidence_level") or "low",
            warning=quality.get("warning") or "",
        )
    )

    for cluster in result.get("clusters", []):
        db.add(
            ClusterResult(
                task_id=task.id,
                cluster_id=cluster["cluster_id"],
                cluster_name=cluster["cluster_name"],
                cluster_size=cluster["cluster_size"],
                cluster_ratio=cluster["cluster_ratio"],
                top_keywords=cluster["top_keywords"],
                sentiment_distribution=cluster["sentiment_distribution"],
                method=cluster.get("method", "rules"),
                is_noise=bool(cluster.get("is_noise", False)),
                representative_comments=cluster.get("representative_comments") or [],
            )
        )

    for representative in result.get("representatives", []):
        clean = clean_by_raw_id.get(str(representative["comment_id"]))
        if clean:
            db.add(
                RepresentativeComment(
                    task_id=task.id,
                    cluster_id=representative["cluster_id"],
                    comment_id=clean.id,
                    reason=representative["reason"],
                )
            )

    insight = result.get("insight_report") or {}
    db.add(
        InsightReport(
            task_id=task.id,
            summary=insight.get("summary", ""),
            positive_insights=insight.get("positive_insights", []),
            negative_insights=insight.get("negative_insights", []),
            key_viewpoints=insight.get("key_viewpoints", []),
            controversies=insight.get("controversies", []),
            news_context_summary=insight.get("news_context_summary", ""),
            context_alignment=insight.get("context_alignment", []),
            fact_opinion_gaps=insight.get("fact_opinion_gaps", []),
            context_media=result.get("context_media_items", []),
            platform_differences=[],
            risks=insight.get("risks", []),
            recommendations=[],
        )
    )
    for card in StrategyCardService().build(result):
        db.add(StrategyCard(task_id=task.id, **card))
    db.flush()
