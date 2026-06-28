from __future__ import annotations

import json
import logging
import time
from typing import Any

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)


class SiliconFlowVisionService:
    """Analyze informative source images through SiliconFlow's multimodal chat API."""

    def __init__(self, client: httpx.Client | None = None) -> None:
        self.settings = get_settings()
        self.client = client

    def analyze_context_media(self, source: dict[str, Any], match_context: dict[str, Any]) -> dict[str, Any]:
        """Return structured evidence for a main-post, news, or official image."""

        image_urls = [url for url in source.get("image_urls", []) if str(url).startswith(("https://", "http://"))][:2]
        if not image_urls:
            return {"status": "no_images", "model": self.settings.siliconflow_vision_model}
        if not self.settings.siliconflow_api_key:
            return {
                "status": "skipped_missing_key",
                "model": self.settings.siliconflow_vision_model,
                "error": "SILICONFLOW_API_KEY is not configured",
            }

        content: list[dict[str, Any]] = [
            {"type": "image_url", "image_url": {"url": url, "detail": "high"}} for url in image_urls
        ]
        content.append({"type": "text", "text": self._prompt(source, match_context)})
        payload = {
            "model": self.settings.siliconflow_vision_model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "你是体育赛事信息图与数据图分析器。只提取图片中清晰可见的信息，不推断不可见事实，"
                        "不识别普通用户身份，也不把来源权威性当作图片内容本身的证明。"
                        "严格输出 JSON object，不要输出 Markdown。"
                    ),
                },
                {"role": "user", "content": content},
            ],
            "max_tokens": 512,
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
                "data_points": self._text_list(parsed.get("data_points"))[:16],
                "relevance": self._choice(parsed.get("relevance"), {"high", "medium", "low", "unrelated"}, "medium"),
                "information_value": self._choice(
                    parsed.get("information_value"), {"high", "medium", "low"}, "low"
                ),
                "confidence": self._choice(parsed.get("confidence"), {"high", "medium", "low"}, "low"),
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
    def _prompt(source: dict[str, Any], match_context: dict[str, Any]) -> str:
        match_name = match_context.get("match_name") or "未命名比赛"
        title = str(source.get("title") or "")[:300]
        text_context = str(source.get("text_context") or "")[:1200]
        authority = str(source.get("authority_level") or "unknown")
        return (
            f"比赛：{match_name}\n来源标题：{title}\n来源级别：{authority}\n来源正文摘要：{text_context}\n"
            "分析主帖、新闻或官网中的图片。优先提取球员数据、球队数据、比分、阵容、伤病、判罚或裁判报告信息，"
            "并按以下 JSON schema 输出："
            '{"summary":"图片中与比赛有关的客观信息摘要","ocr_text":"图片中清晰可见的文字，没有则为空",'
            '"entities":["可见的球队、球员、比分或赛事元素"],'
            '"data_points":["图片中明确可读的统计数字或事实，每项单独列出"],'
            '"relevance":"high|medium|low|unrelated",'
            '"information_value":"high|medium|low","confidence":"high|medium|low"}。'
            "只有能对应当前比赛、球队、球员、裁判或明确赛事数据时 relevance 才能为 high/medium。"
            "information_value 只有在图片包含完整技术统计、数据图表、最终比分、阵容伤病、官方公告或裁判报告时"
            "才能为 high/medium；仅有比赛中途比分的转播截图、纯人物照片、赛场氛围图、表情包或旧比赛梗图"
            "必须为 low。"
            "看不清的数字不要猜；来源正文只能帮助定位，不得替代图片可见内容。"
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
