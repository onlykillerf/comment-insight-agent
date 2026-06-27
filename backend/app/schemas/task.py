from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    """Payload for creating an analysis task."""

    name: str = Field(default="虎扑赛事评论分析", min_length=1)
    domain: str = Field(default="basketball", pattern="^(basketball|football)$")
    platforms: list[str] = Field(default_factory=lambda: ["hupu"])
    board: str = "nba"
    match_name: str = ""
    home_team: str = ""
    away_team: str = ""
    match_stage: str = ""
    match_date: str = ""
    thread_urls: list[str] = Field(default_factory=list)
    news_urls: list[str] = Field(default_factory=list)
    news_context: str = ""
    keywords: list[str] = Field(default_factory=list)
    semantic_query: str = "分析虎扑网友对本场比赛的情绪、争议焦点和主要观点"
    time_range: dict[str, Any] = Field(default_factory=dict)
    max_comments: int = Field(default=120, ge=1, le=5000)
    similarity_threshold: float = Field(default=0.86, ge=0.0, le=1.0)
    language: str = "zh"
    sentiment_focus: str = "all"
    enable_llm: bool = True
    enable_image_analysis: bool = True
    max_image_comments: int = Field(default=6, ge=0, le=20)
    data_source: str = Field(default="mock", pattern="^(mock|hupu_public|csv|json)$")
    source_path: str | None = None


class TaskOut(BaseModel):
    """Task response model."""

    id: int
    name: str
    domain: str
    platforms: list[str]
    board: str
    match_name: str
    home_team: str
    away_team: str
    match_stage: str
    match_date: str
    thread_urls: list[str]
    news_urls: list[str]
    news_context: str
    keywords: list[str]
    semantic_query: str
    time_range: dict[str, Any]
    max_comments: int
    similarity_threshold: float
    language: str
    sentiment_focus: str
    enable_llm: bool
    enable_image_analysis: bool
    max_image_comments: int
    data_source: str
    source_path: str | None
    status: str
    progress: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TaskStatusOut(BaseModel):
    """Current task status and stage progress."""

    task_id: int
    status: str
    progress: dict[str, Any]


class TaskRunResponse(BaseModel):
    """Response returned after a task run is triggered."""

    task_id: int
    status: str
    summary: dict[str, Any]


class CommentOut(BaseModel):
    """Comment API response after cleaning and annotation."""

    id: int
    raw_comment_id: str
    platform: str
    content: str
    cleaned_content: str
    language: str
    quality_score: float
    is_duplicate: bool
    like_count: int
    sentiment_label: str | None = None
    sentiment_score: float | None = None
    painpoint: str | None = None
    positive_attribution: str | None = None
    representative_reason: str | None = None
    image_urls: list[str] = Field(default_factory=list)
    image_analysis: dict[str, Any] = Field(default_factory=dict)


class SentimentOut(BaseModel):
    """Sentiment distribution response."""

    distribution: dict[str, int]
    average_score: float


class PainPointOut(BaseModel):
    """Pain point top-N response."""

    category: str
    count: int
    ratio: float
    examples: list[str]


class PositiveAttributionOut(BaseModel):
    """Positive attribution top-N response."""

    category: str
    count: int
    ratio: float
    examples: list[str]


class ClusterOut(BaseModel):
    """Cluster summary response."""

    cluster_id: int
    cluster_name: str
    cluster_size: int
    cluster_ratio: float
    top_keywords: list[str]
    sentiment_distribution: dict[str, int]
    method: str = "rules"
    is_noise: bool = False
    representative_comments: list[str] = Field(default_factory=list)


class DataQualityOut(BaseModel):
    """Data quality report response."""

    raw_count: int
    clean_count: int
    dedup_count: int
    duplicate_ratio: float
    noise_ratio: float
    language_distribution: dict[str, int]
    sample_confidence_level: str
    warning: str = ""


class WordCloudItem(BaseModel):
    """Weighted word item for word cloud rendering."""

    word: str
    weight: float


class WordCloudsOut(BaseModel):
    """All, positive and negative TF-IDF word clouds."""

    all_words: list[WordCloudItem] = Field(default_factory=list)
    positive_words: list[WordCloudItem] = Field(default_factory=list)
    negative_words: list[WordCloudItem] = Field(default_factory=list)
    explanations: dict[str, str] = Field(default_factory=dict)


class InsightOut(BaseModel):
    """Structured insight report response."""

    summary: str
    positive_insights: list[str]
    negative_insights: list[str]
    key_viewpoints: list[str]
    controversies: list[str]
    news_context_summary: str
    context_alignment: list[str]
    fact_opinion_gaps: list[str]
    risks: list[str]
    context_media: list[dict[str, Any]] = Field(default_factory=list)
