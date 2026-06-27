from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)


class LLMService:
    """Unified LLM provider facade."""

    def __init__(self) -> None:
        self.settings = get_settings()

    def generate_insight(self, context: dict[str, Any]) -> dict[str, Any]:
        """Generate a structured insight report.

        The mock provider is used only when explicitly configured or when no
        provider key is configured.
        """

        if self.settings.llm_provider == "mock" or not self._has_provider_key():
            return self._mock_response(context)
        try:
            return self._provider_response(context)
        except Exception as exc:
            logger.warning("LLM provider failed: %s", exc)
            return self._provider_error_response(exc)

    def _has_provider_key(self) -> bool:
        provider = self.settings.llm_provider.lower()
        if provider == "openai":
            return bool(self.settings.openai_api_key)
        if provider == "deepseek":
            return bool(self.settings.deepseek_api_key)
        if provider == "qwen":
            return bool(self.settings.qwen_api_key)
        if provider in {"siliconflow", "silicon_flow"}:
            return bool(self.settings.siliconflow_api_key)
        return any(
            [
                self.settings.openai_api_key,
                self.settings.deepseek_api_key,
                self.settings.qwen_api_key,
                self.settings.siliconflow_api_key,
            ]
        )

    def _provider_response(self, context: dict[str, Any]) -> dict[str, Any]:
        config = self._provider_config()
        prompt = self._build_prompt(context)
        with httpx.Client(timeout=60) as client:
            response = client.post(
                f"{config['base_url'].rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {config['api_key']}", "Content-Type": "application/json"},
                json={
                    "model": config["model"],
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "你是评论洞察分析专家。只输出一个合法 JSON object，不要输出 Markdown、代码块、解释文字或 Python dict。"
                                "如果模型产生思考过程，请不要把思考过程写入最终答案。"
                                "JSON 字段必须且只能包含 summary, positive_insights, negative_insights, "
                                "platform_differences, risks, recommendations。summary 必须是字符串；其余字段必须是中文字符串数组。"
                            ),
                        },
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.2,
                },
            )
            response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        parsed = self._parse_json_content(content)
        return {
            "summary": self._to_text(parsed.get("summary") or ""),
            "positive_insights": self._to_text_list(parsed.get("positive_insights")),
            "negative_insights": self._to_text_list(parsed.get("negative_insights")),
            "platform_differences": self._to_text_list(parsed.get("platform_differences")),
            "risks": self._to_text_list(parsed.get("risks")),
            "recommendations": self._to_text_list(parsed.get("recommendations")),
        }

    def _provider_config(self) -> dict[str, str]:
        provider = self.settings.llm_provider.lower()
        if provider == "deepseek":
            return {
                "api_key": self.settings.deepseek_api_key or "",
                "base_url": self.settings.llm_base_url or "https://api.deepseek.com",
                "model": self.settings.llm_model or "deepseek-chat",
            }
        if provider == "qwen":
            return {
                "api_key": self.settings.qwen_api_key or "",
                "base_url": self.settings.llm_base_url or "https://dashscope.aliyuncs.com/compatible-mode/v1",
                "model": self.settings.llm_model or "qwen-plus",
            }
        if provider in {"siliconflow", "silicon_flow"}:
            return {
                "api_key": self.settings.siliconflow_api_key or "",
                "base_url": self.settings.llm_base_url or "https://api.siliconflow.cn/v1",
                "model": self.settings.llm_model or "Qwen/Qwen3-8B",
            }
        return {
            "api_key": self.settings.openai_api_key or "",
            "base_url": self.settings.llm_base_url or "https://api.openai.com/v1",
            "model": self.settings.llm_model or "gpt-4o-mini",
        }

    def _build_prompt(self, context: dict[str, Any]) -> str:
        payload = {
            "summary": context.get("summary", {}),
            "source_notes": self._source_notes(context.get("raw_comments", [])),
            "painpoints": context.get("painpoints", []),
            "positive_attributions": context.get("positive_attributions", []),
            "clusters": context.get("clusters", []),
            "representative_comments": context.get("representatives", [])[:12],
        }
        return (
            "请基于以下评论分析中间结果，生成结构化洞察，回答整体情绪、好评来源、"
            "差评痛点、平台差异、高优先级问题、正向卖点、产品优化/内容创意、"
            "舆情风险和下一步验证。\n"
            "严格按这个 JSON schema 输出，不要新增 overall_sentiment、main_topics、key_insights 等字段：\n"
            "{"
            '"summary":"一句话总结整体情绪和核心发现",'
            '"positive_insights":["正向洞察1","正向洞察2"],'
            '"negative_insights":["负向洞察1","负向洞察2"],'
            '"platform_differences":["平台差异1"],'
            '"risks":["风险1","风险2"],'
            '"recommendations":["建议1","建议2","建议3"]'
            "}\n"
            f"{json.dumps(payload, ensure_ascii=False)}"
        )

    def _source_notes(self, raw_comments: list[dict[str, Any]]) -> list[dict[str, Any]]:
        notes: dict[str, dict[str, Any]] = {}
        for comment in raw_comments:
            metadata = comment.get("metadata") or {}
            note_key = str(metadata.get("source_id") or comment.get("source_url") or comment.get("topic") or "")
            if not note_key:
                note_key = str(comment.get("id", ""))
            note = notes.setdefault(
                note_key,
                {
                    "title": metadata.get("note_title") or comment.get("topic") or "",
                    "desc": metadata.get("note_desc") or "",
                    "media_type": metadata.get("note_media_type") or "unknown",
                    "image_count": metadata.get("note_image_count") or 0,
                    "video_count": metadata.get("note_video_count") or 0,
                    "source_query": metadata.get("source_query") or metadata.get("source_keyword") or "",
                    "source_url": comment.get("source_url", ""),
                    "comment_count_sampled": 0,
                    "comment_examples": [],
                },
            )
            note["comment_count_sampled"] += 1
            if len(note["comment_examples"]) < 3:
                note["comment_examples"].append(comment.get("content", ""))
        return list(notes.values())[:16]

    def _parse_json_content(self, content: str) -> dict[str, Any]:
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            start = content.find("{")
            end = content.rfind("}")
            if start >= 0 and end > start:
                return json.loads(content[start : end + 1])
            raise

    def _to_text(self, value: Any) -> str:
        if isinstance(value, str):
            return value
        if isinstance(value, dict):
            return "；".join(f"{key}：{self._to_text(item)}" for key, item in value.items() if item not in (None, "", []))
        if isinstance(value, list):
            return "；".join(self._to_text(item) for item in value if item not in (None, "", []))
        return str(value) if value not in (None, "") else ""

    def _to_text_list(self, value: Any) -> list[str]:
        if value in (None, ""):
            return []
        if isinstance(value, list):
            return [self._to_text(item) for item in value if self._to_text(item)]
        if isinstance(value, dict):
            return [f"{key}：{self._to_text(item)}" for key, item in value.items() if item not in (None, "", [])]
        return [self._to_text(value)]

    def _provider_error_response(self, exc: Exception) -> dict[str, Any]:
        provider = self.settings.llm_provider
        return {
            "summary": f"LLM provider `{provider}` 调用失败，本次未生成模型洞察：{exc}",
            "positive_insights": [],
            "negative_insights": [],
            "platform_differences": [],
            "risks": [f"{provider} provider 当前不可用，请检查额度、限流、账单或模型权限。"],
            "recommendations": ["修复 provider 后重新运行任务，或临时使用 --disable-llm 只跑规则分析。"],
        }

    def _mock_response(self, context: dict[str, Any]) -> dict[str, Any]:
        painpoints = context.get("painpoints", [])
        positives = context.get("positive_attributions", [])
        primary_pain = painpoints[0]["category"] if painpoints else "广告过多"
        primary_positive = positives[0]["category"] if positives else "玩法爽感"
        return {
            "summary": (
                f"本轮评论整体呈现分化：用户认可「{primary_positive}」，"
                f"但负面反馈集中在「{primary_pain}」。建议优先处理高频痛点，"
                "同时把正向卖点转化为内容传播素材。"
            ),
            "positive_insights": [
                f"正向评论主要来自 {primary_positive}，可作为素材和产品页卖点。",
                "点赞较高的评论表达清晰，适合沉淀为典型用户证言。",
            ],
            "negative_insights": [
                f"负向评论优先关注 {primary_pain}，该问题更容易引发连锁差评。",
                "卡顿、强制广告、信息不透明等反馈需要拆成可验证实验。",
            ],
            "platform_differences": [
                "微博评论更情绪化，适合监控舆情风险。",
                "知乎评论更偏原因分析，适合抽取产品优化建议。",
                "虎扑评论更关注赛事/对抗体验和高光内容。",
            ],
            "risks": [
                "若强制广告继续出现在关键体验节点，可能放大负面传播。",
                "若匹配和数值问题没有解释机制，容易形成信任问题。",
            ],
            "recommendations": [
                "优先做广告频率和触发时机 A/B 实验。",
                "将高赞正向评论转化为短视频脚本和商店页卖点。",
                "建立每周评论聚类复盘，追踪新增痛点。",
            ],
        }
