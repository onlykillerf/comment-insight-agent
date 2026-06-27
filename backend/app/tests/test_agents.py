from __future__ import annotations

from app.agents.cleaning_agent import DataCleaningAgent
from app.agents.sentiment_agent import SentimentAgent


def test_cleaning_keeps_short_emotional_text() -> None:
    agent = DataCleaningAgent()
    comments = [{"id": "1", "content": "太爽了👍", "platform": "weibo"}]

    cleaned = agent.run(comments)

    assert len(cleaned) == 1
    assert "太爽了" in cleaned[0]["cleaned_content"]


def test_sentiment_labels_negative_ad_comment() -> None:
    agent = SentimentAgent()

    score = agent.score("刚玩两分钟就弹广告，真的烦")

    assert score < 0
    assert agent.label(score) in {"negative", "strong_negative"}

