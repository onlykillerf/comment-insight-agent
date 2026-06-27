from __future__ import annotations

from collections import Counter
from typing import Any

from app.services.chinese_nlp import tfidf_wordcloud


class VisualizationService:
    """Build frontend-ready chart payloads from workflow outputs."""

    def build(self, context: dict[str, Any]) -> dict[str, Any]:
        """Return chart and word-cloud structures."""

        comments = context.get("comments", [])
        domain = context.get("config", {}).get("domain", "basketball")
        clean_comments = [comment for comment in comments if not comment.get("is_duplicate")]
        sentiments = Counter(comment.get("sentiment", {}).get("label", "neutral") for comment in clean_comments)
        platforms = Counter(comment.get("platform", "unknown") for comment in clean_comments)

        return {
            "comment_trend": [{"date": "demo", "count": len(clean_comments)}],
            "platform_distribution": dict(platforms),
            "sentiment_distribution": dict(sentiments),
            "positive_topn": context.get("positive_attributions", []),
            "painpoint_topn": context.get("painpoints", []),
            "cluster_bubbles": context.get("clusters", []),
            "keyword_wordcloud": tfidf_wordcloud(clean_comments, domain=domain),
            "positive_wordcloud": tfidf_wordcloud(clean_comments, domain=domain, sentiment="positive"),
            "negative_wordcloud": tfidf_wordcloud(clean_comments, domain=domain, sentiment="negative"),
            "wordcloud_explanations": self.wordcloud_explanations(clean_comments),
            "representative_comments": context.get("representatives", []),
        }

    def wordcloud_payload(self, comments: list[dict[str, Any]], domain: str) -> dict[str, Any]:
        """Return a standalone word-cloud payload for API consumers."""

        return {
            "all_words": tfidf_wordcloud(comments, domain=domain),
            "positive_words": tfidf_wordcloud(comments, domain=domain, sentiment="positive"),
            "negative_words": tfidf_wordcloud(comments, domain=domain, sentiment="negative"),
            "explanations": self.wordcloud_explanations(comments),
        }

    def wordcloud_explanations(self, comments: list[dict[str, Any]]) -> dict[str, str]:
        total = len([comment for comment in comments if not comment.get("is_duplicate")])
        negative = len(
            [
                comment
                for comment in comments
                if not comment.get("is_duplicate") and float(comment.get("sentiment", {}).get("score") or 0) < -0.1
            ]
        )
        positive = len(
            [
                comment
                for comment in comments
                if not comment.get("is_duplicate") and float(comment.get("sentiment", {}).get("score") or 0) > 0.1
            ]
        )
        return {
            "all": f"全量词云基于 {total} 条去重评论，用 TF-IDF 并提升领域词权重生成。",
            "positive": f"正向词云只统计 {positive} 条正向评论，用于观察被认可的选题角度。",
            "negative": f"负向词云只统计 {negative} 条负向评论，用于定位争议和风险表达。",
        }
