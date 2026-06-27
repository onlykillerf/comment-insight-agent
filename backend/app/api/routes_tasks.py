from __future__ import annotations

from collections import Counter, defaultdict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import CleanComment, Task
from app.schemas import (
    ClusterOut,
    CommentOut,
    DataQualityOut,
    InsightOut,
    PainPointOut,
    PositiveAttributionOut,
    SentimentOut,
    StrategyCardOut,
    TaskCreate,
    TaskOut,
    TaskRunResponse,
    TaskStatusOut,
    WordCloudsOut,
)
from app.services.persistence import run_and_store_task
from app.services.visualization_service import VisualizationService

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.post("", response_model=TaskOut)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)) -> Task:
    """Create an analysis task."""

    task = Task(
        name=payload.name,
        domain=payload.domain,
        platforms=payload.platforms,
        keywords=payload.keywords,
        semantic_query=payload.semantic_query,
        time_range=payload.time_range,
        max_comments=payload.max_comments,
        similarity_threshold=payload.similarity_threshold,
        language=payload.language,
        sentiment_focus=payload.sentiment_focus,
        enable_llm=payload.enable_llm,
        data_source=payload.data_source,
        source_path=payload.source_path,
        status="created",
        progress={},
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get("", response_model=list[TaskOut])
def list_tasks(db: Session = Depends(get_db)) -> list[Task]:
    """Return all tasks, newest first."""

    return db.query(Task).order_by(Task.created_at.desc()).all()


@router.get("/{task_id}", response_model=TaskOut)
def get_task(task_id: int, db: Session = Depends(get_db)) -> Task:
    """Return task detail."""

    return _get_task_or_404(db, task_id)


@router.post("/{task_id}/run", response_model=TaskRunResponse)
def run_task(task_id: int, db: Session = Depends(get_db)) -> TaskRunResponse:
    """Run the full analysis workflow synchronously for the MVP."""

    task = _get_task_or_404(db, task_id)
    summary = run_and_store_task(db, task)
    return TaskRunResponse(task_id=task.id, status=task.status, summary=summary)


@router.get("/{task_id}/status", response_model=TaskStatusOut)
def get_status(task_id: int, db: Session = Depends(get_db)) -> TaskStatusOut:
    """Return task status."""

    task = _get_task_or_404(db, task_id)
    return TaskStatusOut(task_id=task.id, status=task.status, progress=task.progress or {})


@router.get("/{task_id}/quality", response_model=DataQualityOut)
def get_quality(task_id: int, db: Session = Depends(get_db)) -> DataQualityOut:
    """Return data quality metrics for the task."""

    task = _get_task_or_404(db, task_id)
    report = task.data_quality_report
    if not report:
        raise HTTPException(status_code=404, detail="Data quality report has not been generated")
    return DataQualityOut(
        raw_count=report.raw_count,
        clean_count=report.clean_count,
        dedup_count=report.dedup_count,
        duplicate_ratio=report.duplicate_ratio,
        noise_ratio=report.noise_ratio,
        language_distribution=report.language_distribution,
        sample_confidence_level=report.sample_confidence_level,
        warning=report.warning,
    )


@router.get("/{task_id}/comments", response_model=list[CommentOut])
def get_comments(task_id: int, db: Session = Depends(get_db)) -> list[CommentOut]:
    """Return cleaned comments with annotations."""

    task = _get_task_or_404(db, task_id)
    rows: list[CommentOut] = []
    representative_reasons = {representative.comment_id: representative.reason for representative in task.representatives}
    for comment in task.clean_comments:
        rows.append(
            CommentOut(
                id=comment.id,
                raw_comment_id=comment.raw_comment_id,
                platform=comment.raw_comment.platform,
                content=comment.content,
                cleaned_content=comment.cleaned_content,
                language=comment.language,
                quality_score=comment.quality_score,
                is_duplicate=comment.is_duplicate,
                like_count=comment.raw_comment.like_count,
                sentiment_label=comment.sentiment.label if comment.sentiment else None,
                sentiment_score=comment.sentiment.score if comment.sentiment else None,
                painpoint=comment.painpoint.category if comment.painpoint else None,
                positive_attribution=(
                    comment.positive_attribution.category if comment.positive_attribution else None
                ),
                representative_reason=representative_reasons.get(comment.id),
            )
        )
    return rows


@router.get("/{task_id}/clusters", response_model=list[ClusterOut])
def get_clusters(task_id: int, db: Session = Depends(get_db)) -> list[ClusterOut]:
    """Return cluster summaries."""

    task = _get_task_or_404(db, task_id)
    return [
        ClusterOut(
            cluster_id=row.cluster_id,
            cluster_name=row.cluster_name,
            cluster_size=row.cluster_size,
            cluster_ratio=row.cluster_ratio,
            top_keywords=row.top_keywords,
            sentiment_distribution=row.sentiment_distribution,
            method=row.method,
            is_noise=row.is_noise,
            representative_comments=row.representative_comments,
        )
        for row in task.clusters
    ]


@router.get("/{task_id}/wordclouds", response_model=WordCloudsOut)
def get_wordclouds(task_id: int, db: Session = Depends(get_db)) -> WordCloudsOut:
    """Return TF-IDF word clouds for all, positive and negative comments."""

    task = _get_task_or_404(db, task_id)
    comments = [
        {
            "cleaned_content": comment.cleaned_content,
            "is_duplicate": comment.is_duplicate,
            "sentiment": {
                "label": comment.sentiment.label if comment.sentiment else "neutral",
                "score": comment.sentiment.score if comment.sentiment else 0,
            },
        }
        for comment in task.clean_comments
    ]
    payload = VisualizationService().wordcloud_payload(comments, task.domain)
    return WordCloudsOut(**payload)


@router.get("/{task_id}/sentiment", response_model=SentimentOut)
def get_sentiment(task_id: int, db: Session = Depends(get_db)) -> SentimentOut:
    """Return sentiment distribution."""

    task = _get_task_or_404(db, task_id)
    sentiments = [comment.sentiment for comment in task.clean_comments if comment.sentiment and not comment.is_duplicate]
    distribution = Counter(item.label for item in sentiments)
    average = sum(item.score for item in sentiments) / max(1, len(sentiments))
    return SentimentOut(distribution=dict(distribution), average_score=round(average, 3))


@router.get("/{task_id}/painpoints", response_model=list[PainPointOut])
def get_painpoints(task_id: int, db: Session = Depends(get_db)) -> list[PainPointOut]:
    """Return negative pain point top-N."""

    task = _get_task_or_404(db, task_id)
    return _aggregate_classification(task.clean_comments, "painpoint", PainPointOut)


@router.get("/{task_id}/positive-attributions", response_model=list[PositiveAttributionOut])
def get_positive_attributions(task_id: int, db: Session = Depends(get_db)) -> list[PositiveAttributionOut]:
    """Return positive attribution top-N."""

    task = _get_task_or_404(db, task_id)
    return _aggregate_classification(task.clean_comments, "positive_attribution", PositiveAttributionOut)


@router.get("/{task_id}/insights", response_model=InsightOut)
def get_insights(task_id: int, db: Session = Depends(get_db)) -> InsightOut:
    """Return generated insight report."""

    task = _get_task_or_404(db, task_id)
    report = task.insight_report
    if not report:
        raise HTTPException(status_code=404, detail="Insight report has not been generated")
    return InsightOut(
        summary=report.summary,
        positive_insights=report.positive_insights,
        negative_insights=report.negative_insights,
        platform_differences=report.platform_differences,
        risks=report.risks,
        recommendations=report.recommendations,
    )


@router.get("/{task_id}/strategy-cards", response_model=list[StrategyCardOut])
def get_strategy_cards(task_id: int, db: Session = Depends(get_db)) -> list[StrategyCardOut]:
    """Return generated strategy cards."""

    task = _get_task_or_404(db, task_id)
    return [
        StrategyCardOut(
            id=card.id,
            title=card.title,
            type=card.type,
            priority=card.priority,
            problem_or_opportunity=card.problem_or_opportunity,
            evidence_comments=card.evidence_comments,
            evidence_count=card.evidence_count,
            sample_size=card.sample_size,
            confidence=card.confidence,
            confidence_reason=card.confidence_reason,
            affected_ratio=card.affected_ratio,
            suggested_actions=card.suggested_actions,
            expected_impact=card.expected_impact,
            ab_test_design=card.ab_test_design,
        )
        for card in task.strategy_cards
    ]


def _get_task_or_404(db: Session, task_id: int) -> Task:
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


def _aggregate_classification(
    comments: list[CleanComment], field_name: str, schema_type: type[PainPointOut] | type[PositiveAttributionOut]
) -> list:
    grouped: dict[str, list[CleanComment]] = defaultdict(list)
    candidates = [comment for comment in comments if not comment.is_duplicate]
    total = max(1, len(candidates))
    for comment in candidates:
        result = getattr(comment, field_name)
        if result:
            grouped[result.category].append(comment)
    rows = []
    for category, group in grouped.items():
        examples = [
            comment.cleaned_content for comment in sorted(group, key=lambda item: item.raw_comment.like_count, reverse=True)[:3]
        ]
        rows.append(schema_type(category=category, count=len(group), ratio=round(len(group) / total, 4), examples=examples))
    return sorted(rows, key=lambda row: row.count, reverse=True)
