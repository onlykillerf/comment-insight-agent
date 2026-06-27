from __future__ import annotations

import json
from types import SimpleNamespace

import httpx

from app.agents.media_understanding_agent import MediaUnderstandingAgent
from app.services.vision_service import SiliconFlowVisionService
from app.services.llm_service import LLMService


def test_siliconflow_vision_request_is_bounded_and_structured(monkeypatch) -> None:
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
                                    "summary": "比赛转播截图，画面显示球场和比分栏。",
                                    "ocr_text": "NYK 105 SAS 95",
                                    "entities": ["尼克斯", "马刺"],
                                    "relevance": "high",
                                    "sentiment_cue": "neutral",
                                },
                                ensure_ascii=False,
                            )
                        }
                    }
                ]
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    service = SiliconFlowVisionService(client=client)
    monkeypatch.setattr(
        service,
        "settings",
        SimpleNamespace(
            siliconflow_api_key="test-key",
            siliconflow_vision_model="Qwen/Qwen3.5-4B",
            llm_base_url="https://api.siliconflow.cn/v1",
        ),
    )

    result = service.analyze_comment(
        {
            "content": "看比分",
            "image_urls": [
                "https://i3.hoopchina.com.cn/one.jpg",
                "https://i3.hoopchina.com.cn/two.jpg",
                "https://i3.hoopchina.com.cn/ignored.jpg",
            ],
        },
        {"match_name": "尼克斯 vs 马刺 G1"},
    )

    assert result["status"] == "completed"
    assert result["image_count"] == 2
    assert result["ocr_text"] == "NYK 105 SAS 95"
    assert captured["model"] == "Qwen/Qwen3.5-4B"
    assert captured["enable_thinking"] is False
    image_blocks = [item for item in captured["messages"][1]["content"] if item["type"] == "image_url"]
    assert len(image_blocks) == 2


def test_media_agent_respects_comment_limit_and_builds_analysis_content() -> None:
    class FakeVisionService:
        settings = SimpleNamespace(siliconflow_vision_model="Qwen/Qwen3.5-4B")

        def analyze_comment(self, comment: dict, match_context: dict) -> dict:
            return {
                "status": "completed",
                "model": self.settings.siliconflow_vision_model,
                "summary": f"配图属于{match_context['match_name']}",
                "ocr_text": "105-95",
                "relevance": "high",
            }

    comments = [
        {"content": "低赞", "like_count": 1, "image_urls": ["https://example.com/low.jpg"]},
        {"content": "高赞", "like_count": 20, "image_urls": ["https://example.com/high.jpg"]},
    ]
    result = MediaUnderstandingAgent(service=FakeVisionService()).run(
        comments,
        {"enable_image_analysis": True, "max_image_comments": 1, "match_name": "尼克斯 vs 马刺 G1"},
    )

    assert result[0]["image_analysis"]["status"] == "skipped_limit"
    assert result[1]["image_analysis"]["status"] == "completed"
    assert "配图内容" in result[1]["analysis_content"]
    assert "105-95" in result[1]["analysis_content"]


def test_media_agent_does_not_analyze_the_same_image_twice() -> None:
    class CountingVisionService:
        settings = SimpleNamespace(siliconflow_vision_model="Qwen/Qwen3.5-4B")

        def __init__(self) -> None:
            self.calls = 0

        def analyze_comment(self, comment: dict, match_context: dict) -> dict:
            self.calls += 1
            return {"status": "completed", "model": self.settings.siliconflow_vision_model, "summary": "梗图"}

    service = CountingVisionService()
    shared_url = "https://example.com/shared.gif"
    comments = [
        {"content": "第一条", "like_count": 20, "image_urls": [shared_url]},
        {"content": "第二条", "like_count": 10, "image_urls": [shared_url]},
    ]
    result = MediaUnderstandingAgent(service=service).run(
        comments,
        {"enable_image_analysis": True, "max_image_comments": 2, "match_name": "比赛"},
    )

    assert service.calls == 1
    assert result[0]["image_analysis"]["status"] == "completed"
    assert result[1]["image_analysis"]["status"] == "skipped_duplicate"


def test_vision_service_retries_one_transient_transport_error(monkeypatch) -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise httpx.ReadError("temporary EOF", request=request)
        return httpx.Response(200, json={"choices": [{"message": {"content": '{"summary":"赛场图"}'}}]})

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

    result = service.analyze_comment(
        {"content": "赛场", "image_urls": ["https://example.com/game.jpg"]},
        {"match_name": "比赛"},
    )

    assert calls == 2
    assert result["status"] == "completed"


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
