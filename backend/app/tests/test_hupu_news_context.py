from __future__ import annotations

import json

import pytest

from app.agents.news_context_agent import NewsContextAgent
from app.connectors.base import FetchRequest
from app.connectors.hupu_connector import HupuPublicConnector


def test_hupu_public_page_is_converted_to_comments() -> None:
    payload = {
        "props": {
            "pageProps": {
                "detail": {
                    "breadCrumb": [
                        {"title": "社区", "url": "/"},
                        {"title": "NBA", "url": "/all-nba"},
                        {"title": "马刺专区", "url": "/spurs"},
                        {"title": "G6 赛后", "url": "/123.html"},
                    ],
                    "thread": {
                        "tid": "123",
                        "title": "[赛后]马刺 108-104 尼克斯",
                        "content": "<p>马刺与尼克斯 G6 比赛结束。</p>",
                    },
                    "replies": {
                        "total": 2,
                        "list": [
                            {
                                "pid": "p1",
                                "authorId": "u1",
                                "content": '<p>末节关键球执行很稳。</p><img src="https://i3.hoopchina.com.cn/game-shot.jpg">',
                                "allLightCount": 42,
                                "replyNum": 3,
                                "createdAt": 1780000000000,
                            }
                        ],
                    },
                    "lights": [],
                }
            }
        }
    }
    html = f'<html><script id="__NEXT_DATA__" type="application/json">{json.dumps(payload)}</script></html>'
    request = FetchRequest(
        task_id=1,
        platform="hupu",
        domain="basketball",
        board="nba",
        match_name="马刺 vs 尼克斯 G6",
        home_team="马刺",
        away_team="尼克斯",
        match_stage="总决赛 G6",
        match_date="2026-06-20",
        keywords=["马刺", "尼克斯"],
        semantic_query="赛后讨论",
    )

    comments, total_pages = HupuPublicConnector().parse_page(html, request, "https://bbs.hupu.com/123.html")

    assert total_pages == 2
    assert len(comments) == 1
    assert comments[0]["content"] == "末节关键球执行很稳。"
    assert comments[0]["like_count"] == 42
    assert comments[0]["image_urls"] == ["https://i3.hoopchina.com.cn/game-shot.jpg"]
    assert comments[0]["image_analysis"] == {}
    assert comments[0]["metadata"]["thread_excerpt"] == "马刺与尼克斯 G6 比赛结束。"
    assert comments[0]["metadata"]["match_name"] == "马刺 vs 尼克斯 G6"


def test_hupu_connector_rejects_non_hupu_urls() -> None:
    with pytest.raises(ValueError, match="Unsupported Hupu"):
        HupuPublicConnector()._thread_id("https://example.com/123.html")


def test_news_article_context_is_extracted() -> None:
    html = """
    <html><head>
      <meta property="og:title" content="G6 赛前伤病与系列赛背景">
      <meta name="description" content="主队核心确认出战，系列赛目前 3-2。">
    </head><body><article><p>双方将在第六场继续争夺，客队需要提升篮板保护。</p></article></body></html>
    """

    item = NewsContextAgent().parse_article(html, "https://news.example.com/game-6")

    assert item["title"] == "G6 赛前伤病与系列赛背景"
    assert "系列赛目前 3-2" in item["summary"]
    assert item["status"] == "fetched"


def test_news_context_rejects_private_urls() -> None:
    with pytest.raises(ValueError, match="Private or local"):
        NewsContextAgent()._validate_public_url("http://127.0.0.1/internal")
