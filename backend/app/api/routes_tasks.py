from __future__ import annotations

from collections import Counter, defaultdict

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import CleanComment, Task, UploadedDataset
from app.schemas import (
    ClusterOut,
    CommentOut,
    DataQualityOut,
    InsightOut,
    PainPointOut,
    PositiveAttributionOut,
    SentimentOut,
    TaskCreate,
    TaskOut,
    TaskRunResponse,
    TaskStatusOut,
    WordCloudsOut,
)
from app.services.task_execution_service import task_execution_service
from app.services.visualization_service import VisualizationService

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.post("", response_model=TaskOut)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)) -> Task:
    """Create an analysis task."""

    source_path = payload.source_path
    data_source = payload.data_source
    field_mapping = payload.field_mapping
    if payload.upload_id:
        upload = db.get(UploadedDataset, payload.upload_id)
        if not upload:
            raise HTTPException(status_code=404, detail="上传文件不存在")
        if upload.status != "ready":
            raise HTTPException(status_code=422, detail="请先完成上传文件的字段映射")
        source_path = upload.stored_path
        data_source = upload.source_kind
        field_mapping = upload.field_mapping
    elif payload.data_source in {"csv", "json", "mediacrawler"} and not payload.source_path:
        raise HTTPException(status_code=422, detail="请先在浏览器上传数据文件")

    task = Task(
        name=payload.name,
        domain=payload.domain,
        platforms=["hupu"],
        board=payload.board,
        match_name=payload.match_name,
        home_team=payload.home_team,
        away_team=payload.away_team,
        match_stage=payload.match_stage,
        match_date=payload.match_date,
        thread_urls=payload.thread_urls,
        news_urls=payload.news_urls,
        news_context=payload.news_context,
        keywords=payload.keywords,
        semantic_query=payload.semantic_query,
        time_range=payload.time_range,
        max_comments=payload.max_comments,
        similarity_threshold=payload.similarity_threshold,
        language=payload.language,
        sentiment_focus=payload.sentiment_focus,
        enable_llm=payload.enable_llm,
        llm_mode=payload.llm_mode,
        enable_image_analysis=payload.enable_image_analysis,
        max_image_comments=payload.max_image_comments,
        data_source=data_source,
        source_path=source_path,
        upload_id=payload.upload_id,
        field_mapping=field_mapping,
        status="created",
        progress={},
        error_message="",
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get("", response_model=list[TaskOut])
def list_tasks(db: Session = Depends(get_db)) -> list[Task]:
    """Return focused basketball and football tasks, newest first."""

    return db.query(Task).filter(Task.domain.in_(["basketball", "football"])).order_by(Task.created_at.desc()).all()


@router.get("/{task_id}", response_model=TaskOut)
def get_task(task_id: int, db: Session = Depends(get_db)) -> Task:
    """Return task detail."""

    return _get_task_or_404(db, task_id)


@router.post("/{task_id}/run", response_model=TaskRunResponse, status_code=202)
def run_task(task_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)) -> TaskRunResponse:
    """Queue the analysis and return immediately."""

    task = _get_task_or_404(db, task_id)
    try:
        state = task_execution_service.queue(task.id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    background_tasks.add_task(task_execution_service.start, task.id)
    return TaskRunResponse(task_id=task.id, status=state["status"], summary={})


@router.post("/{task_id}/cancel", response_model=TaskRunResponse, status_code=202)
def cancel_task(task_id: int, db: Session = Depends(get_db)) -> TaskRunResponse:
    _get_task_or_404(db, task_id)
    if not task_execution_service.cancel(task_id):
        raise HTTPException(status_code=409, detail="只有排队中或运行中的任务可以取消")
    db.expire_all()
    task = _get_task_or_404(db, task_id)
    return TaskRunResponse(task_id=task_id, status=task.status, summary={"cancel_requested": True})


@router.post("/{task_id}/retry", response_model=TaskRunResponse, status_code=202)
def retry_task(task_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)) -> TaskRunResponse:
    task = _get_task_or_404(db, task_id)
    if task.status not in {"failed", "cancelled"}:
        raise HTTPException(status_code=409, detail="只有失败或已取消的任务可以重试")
    try:
        state = task_execution_service.queue(task_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    background_tasks.add_task(task_execution_service.start, task_id)
    return TaskRunResponse(task_id=task_id, status=state["status"], summary={})


@router.get("/{task_id}/status", response_model=TaskStatusOut)
def get_status(task_id: int, db: Session = Depends(get_db)) -> TaskStatusOut:
    """Return task status."""

    task = _get_task_or_404(db, task_id)
    return TaskStatusOut(
        task_id=task.id,
        status=task.status,
        progress=task.progress or {},
        error_message=task.error_message or "",
        cancel_requested=task.cancel_requested,
        run_attempt=task.run_attempt,
        queued_at=task.queued_at,
        started_at=task.started_at,
        finished_at=task.finished_at,
    )


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
                cluster_id=comment.cluster_id,
                image_urls=comment.raw_comment.image_urls or [],
                image_analysis=comment.raw_comment.image_analysis or {},
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
        key_viewpoints=report.key_viewpoints,
        controversies=report.controversies,
        news_context_summary=report.news_context_summary,
        context_alignment=report.context_alignment,
        fact_opinion_gaps=report.fact_opinion_gaps,
        risks=report.risks,
        context_media=report.context_media or [],
    )


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
