from __future__ import annotations

import json
from types import SimpleNamespace

import httpx

from app.agents.media_understanding_agent import MediaUnderstandingAgent
from app.services.llm_service import LLMService
from app.services.vision_service import SiliconFlowVisionService


def test_siliconflow_context_vision_request_is_bounded_and_structured(monkeypatch) -> None:
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured.update(json.loads(request.content))
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "summary": "比赛数据图显示最终比分和哈特的技术统计。",
                                    "ocr_text": "NYK 105 SAS 95",
                                    "entities": ["尼克斯", "马刺", "哈特"],
                                    "data_points": ["哈特15篮板", "哈特4抢断"],
                                    "relevance": "high",
                                    "information_value": "high",
                                    "confidence": "high",
                                },
                                ensure_ascii=False,
                            )
                        }
                    }
                ]
            },
        )

    service = SiliconFlowVisionService(client=httpx.Client(transport=httpx.MockTransport(handler)))
    monkeypatch.setattr(
        service,
        "settings",
        SimpleNamespace(
            siliconflow_api_key="test-key",
            siliconflow_vision_model="Qwen/Qwen3.5-4B",
            llm_base_url="https://api.siliconflow.cn/v1",
        ),
    )

    result = service.analyze_context_media(
        {
            "title": "[流言板]哈特季后赛数据",
            "text_context": "来源：NBA官网。哈特得到15篮板4抢断。",
            "authority_level": "official_reference",
            "image_urls": [
                "https://i3.hoopchina.com.cn/stat-one.png",
                "https://i3.hoopchina.com.cn/stat-two.png",
                "https://i3.hoopchina.com.cn/ignored.png",
            ],
        },
        {"match_name": "尼克斯 vs 马刺 G1"},
    )

    assert result["status"] == "completed"
    assert result["image_count"] == 2
    assert result["data_points"] == ["哈特15篮板", "哈特4抢断"]
    assert captured["model"] == "Qwen/Qwen3.5-4B"
    assert captured["enable_thinking"] is False
    image_blocks = [item for item in captured["messages"][1]["content"] if item["type"] == "image_url"]
    assert len(image_blocks) == 2
    assert all(item["image_url"]["detail"] == "high" for item in image_blocks)


def test_media_agent_uses_main_post_image_and_ignores_reply_image() -> None:
    class FakeVisionService:
        settings = SimpleNamespace(siliconflow_vision_model="Qwen/Qwen3.5-4B")

        def analyze_context_media(self, source: dict, match_context: dict) -> dict:
            return {
                "status": "completed",
                "model": self.settings.siliconflow_vision_model,
                "summary": "哈特数据统计图",
                "ocr_text": "15 REB 4 STL",
                "data_points": ["15篮板", "4抢断"],
                "relevance": "high",
                "information_value": "high",
                "confidence": "high",
            }

    comments = [
        {
            "content": "评论区回复",
            "image_urls": ["https://i3.hoopchina.com.cn/reply-meme.gif"],
            "source_url": "https://bbs.hupu.com/123.html",
            "metadata": {
                "thread_id": "123",
                "thread_title": "[流言板]哈特15篮板4抢断，数据统计来自NBA官网",
                "thread_excerpt": "哈特本场得到15篮板4抢断，来源：NBA官网。",
                "thread_image_urls": ["https://i3.hoopchina.com.cn/hart-stat.png"],
            },
        }
    ]
    result = MediaUnderstandingAgent(service=FakeVisionService()).run(
        comments,
        [],
        {
            "enable_image_analysis": True,
            "max_image_comments": 2,
            "match_name": "尼克斯 vs 马刺 G1",
            "home_team": "马刺",
            "away_team": "尼克斯",
        },
    )

    assert len(result) == 1
    assert result[0]["image_urls"] == ["https://i3.hoopchina.com.cn/hart-stat.png"]
    assert "reply-meme" not in json.dumps(result, ensure_ascii=False)
    assert result[0]["authority_level"] == "official_reference"
    assert result[0]["included_in_summary"] is True


def test_media_agent_rejects_low_information_main_post_image() -> None:
    comments = [
        {
            "content": "普通回复",
            "source_url": "https://bbs.hupu.com/456.html",
            "metadata": {
                "thread_id": "456",
                "thread_title": "赛后随便聊聊",
                "thread_excerpt": "大家怎么看？",
                "thread_image_urls": ["https://i3.hoopchina.com.cn/player-photo.jpg"],
            },
        }
    ]

    result = MediaUnderstandingAgent().run(
        comments,
        [],
        {"enable_image_analysis": True, "max_image_comments": 2, "match_name": "尼克斯 vs 马刺 G1"},
    )

    assert result == []


def test_media_agent_rejects_stats_borrowed_from_text_when_image_is_only_a_portrait() -> None:
    class PortraitVisionService:
        settings = SimpleNamespace(siliconflow_vision_model="Qwen/Qwen3.5-4B")

        def analyze_context_media(self, source: dict, match_context: dict) -> dict:
            return {
                "status": "completed",
                "model": self.settings.siliconflow_vision_model,
                "summary": "哈特人物照片",
                "ocr_text": "NEW YORK 3",
                "data_points": ["15篮板", "4抢断"],
                "relevance": "high",
                "information_value": "medium",
                "confidence": "high",
            }

    comments = [
        {
            "content": "回复",
            "source_url": "https://bbs.hupu.com/10.html",
            "metadata": {
                "thread_id": "10",
                "thread_title": "[流言板]哈特数据统计来自NBA官网",
                "thread_excerpt": "哈特15篮板4抢断。",
                "thread_image_urls": ["https://i3.hoopchina.com.cn/hart.png"],
            },
        }
    ]
    result = MediaUnderstandingAgent(service=PortraitVisionService()).run(
        comments,
        [],
        {"enable_image_analysis": True, "max_image_comments": 1, "match_name": "比赛"},
    )

    assert result[0]["included_in_summary"] is False
    assert "OCR" in result[0]["exclusion_reason"]


def test_media_agent_respects_total_image_budget_and_prioritizes_png() -> None:
    class CountingVisionService:
        settings = SimpleNamespace(siliconflow_vision_model="Qwen/Qwen3.5-4B")

        def __init__(self) -> None:
            self.images: list[str] = []

        def analyze_context_media(self, source: dict, match_context: dict) -> dict:
            self.images.extend(source["image_urls"])
            return {
                "status": "completed",
                "model": self.settings.siliconflow_vision_model,
                "summary": "统计图",
                "data_points": ["数据"],
                "relevance": "high",
                "information_value": "high",
                "confidence": "medium",
            }

    service = CountingVisionService()
    comments = [
        {
            "content": "回复",
            "source_url": "https://bbs.hupu.com/789.html",
            "metadata": {
                "thread_id": "789",
                "thread_title": "球员投篮命中率数据统计",
                "thread_excerpt": "球队进攻效率与三分命中率统计。",
                "thread_image_urls": [
                    "https://i3.hoopchina.com.cn/photo.jpg",
                    "https://i3.hoopchina.com.cn/chart.png",
                    "https://i3.hoopchina.com.cn/reaction.gif",
                ],
            },
        }
    ]
    MediaUnderstandingAgent(service=service).run(
        comments,
        [],
        {"enable_image_analysis": True, "max_image_comments": 1, "match_name": "比赛"},
    )

    assert service.images == ["https://i3.hoopchina.com.cn/chart.png"]


def test_live_scoreboard_ocr_is_not_treated_as_summary_evidence() -> None:
    assert not MediaUnderstandingAgent._has_visual_information(
        {"ocr_text": "ESPN NY 8 SA 2 1st 9:22 Finals GAME 1"}
    )


def test_vision_service_retries_one_transient_transport_error(monkeypatch) -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise httpx.ReadError("temporary EOF", request=request)
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": '{"summary":"数据图","relevance":"high","information_value":"high"}'
                        }
                    }
                ]
            },
        )

    service = SiliconFlowVisionService(client=httpx.Client(transport=httpx.MockTransport(handler)))
    monkeypatch.setattr(
        service,
        "settings",
        SimpleNamespace(
            siliconflow_api_key="test-key",
            siliconflow_vision_model="Qwen/Qwen3.5-4B",
            llm_base_url="https://api.siliconflow.cn/v1",
        ),
    )
    monkeypatch.setattr("app.services.vision_service.time.sleep", lambda _: None)

    result = service.analyze_context_media(
        {"title": "球队数据", "image_urls": ["https://example.com/stat.png"]},
        {"match_name": "比赛"},
    )

    assert calls == 2
    assert result["status"] == "completed"


def test_llm_visual_evidence_only_uses_approved_context_media() -> None:
    evidence = LLMService._context_media_evidence(
        [
            {
                "source_kind": "hupu_thread",
                "title": "球队数据",
                "source_url": "https://bbs.hupu.com/1.html",
                "authority_level": "official_reference",
                "selection_reasons": ["数据统计"],
                "summary": "统计图",
                "data_points": ["15篮板"],
                "included_in_summary": True,
            },
            {"title": "人物照片", "included_in_summary": False},
        ]
    )

    assert len(evidence) == 1
    assert evidence[0]["title"] == "球队数据"


def test_llm_outcome_guard_removes_result_contradiction() -> None:
    service = LLMService()
    context = {
        "config": {
            "match_name": "尼克斯 vs 马刺 G1",
            "home_team": "马刺",
            "away_team": "尼克斯",
        },
        "news_context_items": [
            {"status": "provided", "summary": "尼克斯客场 105-95 击败马刺，系列赛 1-0 领先。"}
        ],
        "clusters": [{"cluster_name": "篮板与防守", "is_noise": False}],
    }
    result = service._apply_outcome_guard(
        {
            "summary": "部分球迷对尼克斯的失利表示不满。",
            "positive_insights": [],
            "negative_insights": ["尼克斯失利源于进攻问题"],
            "key_viewpoints": [],
            "controversies": [],
            "context_alignment": [],
            "fact_opinion_gaps": [],
            "risks": [],
        },
        context,
    )

    assert "尼克斯的失利" not in result["summary"]
    assert result["negative_insights"] == []
    assert any("事实护栏" in item for item in result["fact_opinion_gaps"])
