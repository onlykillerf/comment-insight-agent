from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TimestampMixin:
    """Adds created_at and updated_at timestamps."""

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class Task(TimestampMixin, Base):
    """Analysis task configured by a user."""

    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    domain: Mapped[str] = mapped_column(String(50), default="basketball", nullable=False)
    platforms: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    board: Mapped[str] = mapped_column(String(80), default="nba", nullable=False)
    match_name: Mapped[str] = mapped_column(String(240), default="", nullable=False)
    home_team: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    away_team: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    match_stage: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    match_date: Mapped[str] = mapped_column(String(40), default="", nullable=False)
    thread_urls: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    news_urls: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    news_context: Mapped[str] = mapped_column(Text, default="", nullable=False)
    keywords: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    semantic_query: Mapped[str] = mapped_column(Text, default="", nullable=False)
    time_range: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    max_comments: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    similarity_threshold: Mapped[float] = mapped_column(Float, default=0.86, nullable=False)
    language: Mapped[str] = mapped_column(String(30), default="zh", nullable=False)
    sentiment_focus: Mapped[str] = mapped_column(String(30), default="all", nullable=False)
    enable_llm: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    enable_image_analysis: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    max_image_comments: Mapped[int] = mapped_column(Integer, default=6, nullable=False)
    data_source: Mapped[str] = mapped_column(String(40), default="mock", nullable=False)
    source_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="created", nullable=False)
    progress: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    raw_comments: Mapped[list["RawComment"]] = relationship(cascade="all, delete-orphan", back_populates="task")
    clean_comments: Mapped[list["CleanComment"]] = relationship(cascade="all, delete-orphan", back_populates="task")
    clusters: Mapped[list["ClusterResult"]] = relationship(cascade="all, delete-orphan", back_populates="task")
    representatives: Mapped[list["RepresentativeComment"]] = relationship(
        cascade="all, delete-orphan", back_populates="task"
    )
    data_quality_report: Mapped["DataQualityReport | None"] = relationship(
        cascade="all, delete-orphan", back_populates="task", uselist=False
    )
    insight_report: Mapped["InsightReport | None"] = relationship(
        cascade="all, delete-orphan", back_populates="task", uselist=False
    )


class RawComment(Base):
    """Original comment payload normalized by connectors."""

    __tablename__ = "raw_comments"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), index=True, nullable=False)
    platform: Mapped[str] = mapped_column(String(80), nullable=False)
    topic: Mapped[str] = mapped_column(String(200), default="", nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    author_hash: Mapped[str] = mapped_column(String(100), default="", nullable=False)
    like_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reply_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    publish_time: Mapped[str] = mapped_column(String(50), default="", nullable=False)
    source_url: Mapped[str] = mapped_column(Text, default="", nullable=False)
    parent_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    image_urls: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    image_analysis: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, default=dict, nullable=False)

    task: Mapped[Task] = relationship(back_populates="raw_comments")
    clean_comment: Mapped["CleanComment | None"] = relationship(back_populates="raw_comment", uselist=False)


class CleanComment(Base):
    """Cleaned comment prepared for analysis."""

    __tablename__ = "clean_comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), index=True, nullable=False)
    raw_comment_id: Mapped[str] = mapped_column(ForeignKey("raw_comments.id"), index=True, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    cleaned_content: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(String(30), default="zh", nullable=False)
    quality_score: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    is_duplicate: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    duplicate_group_id: Mapped[str | None] = mapped_column(String(80), nullable=True)

    task: Mapped[Task] = relationship(back_populates="clean_comments")
    raw_comment: Mapped[RawComment] = relationship(back_populates="clean_comment")
    embedding: Mapped["CommentEmbedding | None"] = relationship(back_populates="comment", uselist=False)
    sentiment: Mapped["SentimentResult | None"] = relationship(back_populates="comment", uselist=False)
    painpoint: Mapped["PainPointResult | None"] = relationship(back_populates="comment", uselist=False)
    positive_attribution: Mapped["PositiveAttributionResult | None"] = relationship(
        back_populates="comment", uselist=False
    )


class CommentEmbedding(Base):
    """Pointer to an embedding stored in the vector layer."""

    __tablename__ = "comment_embeddings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    comment_id: Mapped[int] = mapped_column(ForeignKey("clean_comments.id"), index=True, nullable=False)
    vector_store_id: Mapped[str] = mapped_column(String(120), nullable=False)
    embedding_model: Mapped[str] = mapped_column(String(120), nullable=False)
    vector: Mapped[list[float]] = mapped_column(JSON, default=list, nullable=False)

    comment: Mapped[CleanComment] = relationship(back_populates="embedding")


class SentimentResult(Base):
    """Sentiment label and score for a cleaned comment."""

    __tablename__ = "sentiment_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    comment_id: Mapped[int] = mapped_column(ForeignKey("clean_comments.id"), index=True, nullable=False)
    label: Mapped[str] = mapped_column(String(40), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.7, nullable=False)

    comment: Mapped[CleanComment] = relationship(back_populates="sentiment")


class PainPointResult(Base):
    """Negative comment pain point classification."""

    __tablename__ = "painpoint_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    comment_id: Mapped[int] = mapped_column(ForeignKey("clean_comments.id"), index=True, nullable=False)
    category: Mapped[str] = mapped_column(String(120), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.7, nullable=False)
    reason: Mapped[str] = mapped_column(Text, default="", nullable=False)

    comment: Mapped[CleanComment] = relationship(back_populates="painpoint")


class PositiveAttributionResult(Base):
    """Positive comment attribution classification."""

    __tablename__ = "positive_attribution_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    comment_id: Mapped[int] = mapped_column(ForeignKey("clean_comments.id"), index=True, nullable=False)
    category: Mapped[str] = mapped_column(String(120), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.7, nullable=False)
    reason: Mapped[str] = mapped_column(Text, default="", nullable=False)

    comment: Mapped[CleanComment] = relationship(back_populates="positive_attribution")


class ClusterResult(Base):
    """Topic cluster summary."""

    __tablename__ = "cluster_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), index=True, nullable=False)
    cluster_id: Mapped[int] = mapped_column(Integer, nullable=False)
    cluster_name: Mapped[str] = mapped_column(String(160), nullable=False)
    cluster_size: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cluster_ratio: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    top_keywords: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    sentiment_distribution: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    method: Mapped[str] = mapped_column(String(40), default="rules", nullable=False)
    is_noise: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    representative_comments: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)

    task: Mapped[Task] = relationship(back_populates="clusters")


class RepresentativeComment(Base):
    """Representative comment selected from a cluster."""

    __tablename__ = "representative_comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), index=True, nullable=False)
    cluster_id: Mapped[int] = mapped_column(Integer, nullable=False)
    comment_id: Mapped[int] = mapped_column(ForeignKey("clean_comments.id"), index=True, nullable=False)
    reason: Mapped[str] = mapped_column(Text, default="", nullable=False)

    task: Mapped[Task] = relationship(back_populates="representatives")


class InsightReport(Base):
    """LLM or MockLLM generated structured insight report."""

    __tablename__ = "insight_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), index=True, nullable=False, unique=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    positive_insights: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    negative_insights: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    key_viewpoints: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    controversies: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    news_context_summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    context_alignment: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    fact_opinion_gaps: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    # Retained internally so existing SQLite databases remain insert-compatible.
    platform_differences: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    risks: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    recommendations: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)

    task: Mapped[Task] = relationship(back_populates="insight_report")


class DataQualityReport(Base):
    """Sample quality metrics that bound how much the analysis can be trusted."""

    __tablename__ = "data_quality_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), index=True, nullable=False, unique=True)
    raw_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    clean_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    dedup_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    duplicate_ratio: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    noise_ratio: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    language_distribution: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    sample_confidence_level: Mapped[str] = mapped_column(String(30), default="low", nullable=False)
    warning: Mapped[str] = mapped_column(Text, default="", nullable=False)

    task: Mapped[Task] = relationship(back_populates="data_quality_report")
