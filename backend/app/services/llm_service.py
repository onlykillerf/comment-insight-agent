from __future__ import annotations

import json
import logging
import re
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
                                "必须严格区分新闻事实背景与网友主观观点，不得把评论当成事实。"
                                "JSON 字段必须且只能包含 summary, positive_insights, negative_insights, "
                                "key_viewpoints, controversies, news_context_summary, context_alignment, "
                                "fact_opinion_gaps, risks。summary 与 news_context_summary 必须是字符串；其余字段必须是中文字符串数组。"
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
        result = {
            "summary": self._to_text(parsed.get("summary") or ""),
            "positive_insights": self._to_text_list(parsed.get("positive_insights")),
            "negative_insights": self._to_text_list(parsed.get("negative_insights")),
            "key_viewpoints": self._to_text_list(parsed.get("key_viewpoints")),
            "controversies": self._to_text_list(parsed.get("controversies")),
            "news_context_summary": self._to_text(parsed.get("news_context_summary") or ""),
            "context_alignment": self._to_text_list(parsed.get("context_alignment")),
            "fact_opinion_gaps": self._to_text_list(parsed.get("fact_opinion_gaps")),
            "risks": self._to_text_list(parsed.get("risks")),
        }
        return self._apply_outcome_guard(result, context)

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
            "match": {
                key: context.get("config", {}).get(key, "")
                for key in ["domain", "board", "match_name", "home_team", "away_team", "match_stage", "match_date"]
            },
            "data_quality": context.get("data_quality_report", {}),
            "hupu_threads": self._source_notes(context.get("raw_comments", [])),
            "visual_evidence": self._visual_evidence(context.get("raw_comments", [])),
            "news_context": context.get("news_context_items", []),
            "negative_labels": context.get("painpoints", []),
            "positive_labels": context.get("positive_attributions", []),
            "clusters": context.get("clusters", []),
            "representative_comments": context.get("representatives", [])[:12],
        }
        return (
            "请基于虎扑比赛评论的结构化分析结果生成赛事舆情洞察。新闻内容只作为事实背景，"
            "评论及配图分析只代表抽样球迷观点；配图摘要是模型对可见内容的辅助描述，不得当作独立事实来源。"
            "比分、胜负和系列赛状态只能复述 news_context 或帖子中的明确事实，不能根据评论情绪反推；"
            "遇到‘输了’等省略主语的帖子标题时，不得自行猜测具体是哪支球队。输出前必须核对球队与赛果是否一致。"
            "分析整体情绪、支持与批评理由、主要争议、新闻背景与评论的"
            "一致或冲突之处，以及样本和舆情风险。不要生成运营策略、行动建议或 A/B 实验。\n"
            "严格按以下 JSON schema 输出，不要新增字段：\n"
            "{"
            '"summary":"一句话总结整体情绪和核心发现",'
            '"positive_insights":["正向洞察1","正向洞察2"],'
            '"negative_insights":["负向洞察1","负向洞察2"],'
            '"key_viewpoints":["主要观点1","主要观点2"],'
            '"controversies":["争议焦点1","争议焦点2"],'
            '"news_context_summary":"新闻事实背景摘要；没有新闻时明确说明",'
            '"context_alignment":["评论与新闻背景一致或冲突之处"],'
            '"fact_opinion_gaps":["事实与主观判断之间的缺口"],'
            '"risks":["样本或舆情解读风险1"]'
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
                    "title": metadata.get("thread_title") or metadata.get("note_title") or comment.get("topic") or "",
                    "desc": metadata.get("thread_excerpt") or metadata.get("note_desc") or "",
                    "board": metadata.get("board") or "",
                    "source_url": comment.get("source_url", ""),
                    "comment_count_sampled": 0,
                    "comment_examples": [],
                },
            )
            note["comment_count_sampled"] += 1
            if len(note["comment_examples"]) < 3:
                note["comment_examples"].append(comment.get("content", ""))
        return list(notes.values())[:16]

    @staticmethod
    def _visual_evidence(raw_comments: list[dict[str, Any]]) -> list[dict[str, Any]]:
        evidence: list[dict[str, Any]] = []
        for comment in raw_comments:
            analysis = comment.get("image_analysis") or {}
            if analysis.get("status") != "completed":
                continue
            evidence.append(
                {
                    "comment_id": comment.get("id"),
                    "comment_text": str(comment.get("content") or "")[:500],
                    "source_url": comment.get("source_url", ""),
                    "image_urls": list(comment.get("image_urls") or [])[:2],
                    "visual_summary": analysis.get("summary", ""),
                    "ocr_text": analysis.get("ocr_text", ""),
                    "relevance": analysis.get("relevance", ""),
                    "sentiment_cue": analysis.get("sentiment_cue", ""),
                    "model": analysis.get("model", ""),
                }
            )
        return evidence[:8]

    def _apply_outcome_guard(self, result: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        winner, loser = self._explicit_outcome(context)
        if not winner or not loser:
            return result

        losing_terms = "失利|输球|落败|败北|败给"
        winning_terms = "获胜|取胜|赢球|战胜|击败|力克"
        conflict_patterns = [
            re.compile(rf"{re.escape(winner)}[^。；，,]{{0,16}}(?:{losing_terms})"),
            re.compile(rf"{re.escape(loser)}[^。；，,]{{0,16}}(?:{winning_terms})"),
        ]

        def conflicts(text: str) -> bool:
            return any(pattern.search(text) for pattern in conflict_patterns)

        changed = False
        if conflicts(str(result.get("summary") or "")):
            config = context.get("config", {})
            match_name = config.get("match_name") or "本场比赛"
            topics = [
                str(item.get("cluster_name") or "").split("｜", 1)[0]
                for item in context.get("clusters", [])
                if item.get("cluster_name") and not item.get("is_noise")
            ][:2]
            focus = "、".join(topics) or "球员表现与比赛过程"
            result["summary"] = f"{match_name} 的虎扑抽样讨论主要围绕{focus}展开；胜负与比分以新闻背景为准。"
            changed = True

        for field in [
            "positive_insights",
            "negative_insights",
            "key_viewpoints",
            "controversies",
            "context_alignment",
            "risks",
        ]:
            items = [str(item) for item in result.get(field, [])]
            filtered = [item for item in items if not conflicts(item)]
            if len(filtered) != len(items):
                result[field] = filtered
                changed = True

        if changed:
            gaps = list(result.get("fact_opinion_gaps") or [])
            gaps.append("模型草稿中与明确赛果冲突的表述已由事实护栏过滤。")
            result["fact_opinion_gaps"] = list(dict.fromkeys(gaps))
        return result

    @staticmethod
    def _explicit_outcome(context: dict[str, Any]) -> tuple[str, str]:
        config = context.get("config", {})
        teams = [str(config.get(key) or "").strip() for key in ["home_team", "away_team"]]
        if not all(teams):
            return "", ""
        source_text = "\n".join(
            str(item.get("summary") or "")
            for item in context.get("news_context_items", [])
            if item.get("status") != "error"
        )
        for winner, loser in [(teams[0], teams[1]), (teams[1], teams[0])]:
            pattern = re.compile(
                rf"{re.escape(winner)}[^。；\n]{{0,50}}(?:击败|战胜|力克){re.escape(loser)}"
            )
            if pattern.search(source_text):
                return winner, loser
        return "", ""

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
            "key_viewpoints": [],
            "controversies": [],
            "news_context_summary": "",
            "context_alignment": [],
            "fact_opinion_gaps": [],
            "risks": [f"{provider} provider 当前不可用，请检查额度、限流、账单或模型权限。"],
        }

    def _mock_response(self, context: dict[str, Any]) -> dict[str, Any]:
        painpoints = context.get("painpoints", [])
        positives = context.get("positive_attributions", [])
        primary_pain = painpoints[0]["category"] if painpoints else "比赛争议"
        primary_positive = positives[0]["category"] if positives else "比赛观赏性"
        config = context.get("config", {})
        match_name = config.get("match_name") or "本场比赛"
        news_items = [item for item in context.get("news_context_items", []) if item.get("status") != "error"]
        clusters = [item for item in context.get("clusters", []) if not item.get("is_noise")]
        return {
            "summary": (
                f"{match_name} 的虎扑评论整体呈现分化：正向讨论集中在「{primary_positive}」，"
                f"负向讨论主要围绕「{primary_pain}」。该结论仅代表当前去重样本。"
            ),
            "positive_insights": [
                f"认可声音主要围绕「{primary_positive}」展开。",
                "高赞评论更集中于关键回合、球员发挥和比赛过程。",
            ],
            "negative_insights": [
                f"负向声音主要聚焦「{primary_pain}」。",
                "强情绪表达可能放大判罚、球员失误或教练调整相关争论。",
            ],
            "key_viewpoints": [item.get("cluster_name", "") for item in clusters[:3] if item.get("cluster_name")],
            "controversies": [f"当前争议最集中于「{primary_pain}」。"],
            "news_context_summary": (
                f"已读取 {len(news_items)} 条用户指定的新闻或比赛背景。"
                if news_items
                else "本次未提供相关新闻背景，洞察仅基于帖子与评论样本。"
            ),
            "context_alignment": [
                "MockLLM 不对新闻与评论的一致性作事实判断；配置真实 LLM 后可生成上下文对照。"
            ],
            "fact_opinion_gaps": ["球迷对判罚、战术和球员责任的判断属于观点，需要结合比赛数据与可靠报道核对。"],
            "risks": [
                "虎扑单帖用户构成并不代表全部球迷，跨帖子结论应结合样本量和重复率阅读。",
                "高亮回复更容易被采集和看见，可能造成观点热度偏差。",
            ],
        }
