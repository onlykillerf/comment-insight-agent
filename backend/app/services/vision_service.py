from __future__ import annotations

import json
import logging
import time
from typing import Any

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)


class SiliconFlowVisionService:
    """Analyze public comment images through SiliconFlow's multimodal chat API."""

    def __init__(self, client: httpx.Client | None = None) -> None:
        self.settings = get_settings()
        self.client = client

    def analyze_comment(self, comment: dict[str, Any], match_context: dict[str, Any]) -> dict[str, Any]:
        """Return bounded structured visual evidence for one comment."""

        image_urls = [url for url in comment.get("image_urls", []) if str(url).startswith(("https://", "http://"))][:2]
        if not image_urls:
            return {"status": "no_images", "model": self.settings.siliconflow_vision_model}
        if not self.settings.siliconflow_api_key:
            return {
                "status": "skipped_missing_key",
                "model": self.settings.siliconflow_vision_model,
                "error": "SILICONFLOW_API_KEY is not configured",
            }

        content: list[dict[str, Any]] = [
            {"type": "image_url", "image_url": {"url": url, "detail": "low"}} for url in image_urls
        ]
        content.append({"type": "text", "text": self._prompt(comment, match_context)})
        payload = {
            "model": self.settings.siliconflow_vision_model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "你是体育社区评论配图分析器。只描述图片中可见内容，不推断不可见事实，不识别普通用户身份。"
                        "严格输出 JSON object，不要输出 Markdown。"
                    ),
                },
                {"role": "user", "content": content},
            ],
            "max_tokens": 384,
            "temperature": 0,
            "enable_thinking": False,
        }
        try:
            response = self._post(payload)
            response.raise_for_status()
            body = response.json()
            raw_content = str(body["choices"][0]["message"].get("content") or "").strip()
            parsed = self._parse_json(raw_content)
            return {
                "status": "completed",
                "model": self.settings.siliconflow_vision_model,
                "image_count": len(image_urls),
                "summary": self._text(parsed.get("summary") or raw_content)[:800],
                "ocr_text": self._text(parsed.get("ocr_text"))[:500],
                "entities": self._text_list(parsed.get("entities"))[:12],
                "relevance": self._choice(parsed.get("relevance"), {"high", "medium", "low", "unrelated"}, "medium"),
                "sentiment_cue": self._choice(
                    parsed.get("sentiment_cue"), {"positive", "neutral", "negative", "unclear"}, "unclear"
                ),
            }
        except Exception as exc:
            logger.warning("SiliconFlow image analysis failed: %s", exc)
            return {
                "status": "error",
                "model": self.settings.siliconflow_vision_model,
                "image_count": len(image_urls),
                "error": str(exc)[:300],
            }

    def _post(self, payload: dict[str, Any]) -> httpx.Response:
        url = f"{(self.settings.llm_base_url or 'https://api.siliconflow.cn/v1').rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.settings.siliconflow_api_key}",
            "Content-Type": "application/json",
        }
        for attempt in range(2):
            try:
                if self.client is not None:
                    response = self.client.post(url, headers=headers, json=payload, timeout=90)
                else:
                    with httpx.Client(timeout=90) as client:
                        response = client.post(url, headers=headers, json=payload)
                if response.status_code == 429 or response.status_code >= 500:
                    response.raise_for_status()
                return response
            except (httpx.TransportError, httpx.HTTPStatusError):
                if attempt == 1:
                    raise
                time.sleep(0.8)
        raise RuntimeError("SiliconFlow image analysis retry exhausted")

    @staticmethod
    def _prompt(comment: dict[str, Any], match_context: dict[str, Any]) -> str:
        match_name = match_context.get("match_name") or "未命名比赛"
        comment_text = str(comment.get("content") or "")[:500]
        return (
            f"比赛：{match_name}\n评论文字：{comment_text}\n"
            "分析评论配图，并按以下 JSON schema 输出："
            '{"summary":"图片可见内容的客观摘要","ocr_text":"图片中清晰可见的文字，没有则为空",'
            '"entities":["可见的球队、球员、比分或赛事元素"],'
            '"relevance":"high|medium|low|unrelated",'
            '"sentiment_cue":"positive|neutral|negative|unclear"}。'
            "relevance 必须针对当前比赛判断：只有能直接对应本场球队、球员、比分或比赛画面时才为 high；"
            "其他篮球旧图、泛体育图或借图表达归为 medium/low，纯表情包和无关人物归为 unrelated。"
            "不要根据球衣或模糊人脸猜测普通用户身份；无法确认的球员写成未知球员。"
        )

    @staticmethod
    def _parse_json(content: str) -> dict[str, Any]:
        if not content:
            return {}
        cleaned = content.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        try:
            value = json.loads(cleaned)
            return value if isinstance(value, dict) else {}
        except json.JSONDecodeError:
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start >= 0 and end > start:
                try:
                    value = json.loads(cleaned[start : end + 1])
                    return value if isinstance(value, dict) else {}
                except json.JSONDecodeError:
                    pass
        return {"summary": content}

    @staticmethod
    def _text(value: Any) -> str:
        if isinstance(value, str):
            return value.strip()
        if isinstance(value, list):
            return "；".join(str(item).strip() for item in value if str(item).strip())
        return str(value).strip() if value not in (None, "") else ""

    @classmethod
    def _text_list(cls, value: Any) -> list[str]:
        if isinstance(value, list):
            return [cls._text(item) for item in value if cls._text(item)]
        text = cls._text(value)
        return [text] if text else []

    @staticmethod
    def _choice(value: Any, allowed: set[str], fallback: str) -> str:
        normalized = str(value or "").strip().lower()
        return normalized if normalized in allowed else fallback
