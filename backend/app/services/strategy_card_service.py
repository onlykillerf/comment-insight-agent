from __future__ import annotations

from collections import defaultdict
from typing import Any


class StrategyCardService:
    """Build deterministic, evidence-grounded sports content strategy cards."""

    def build(self, result: dict[str, Any]) -> list[dict[str, Any]]:
        comments = [item for item in result.get("comments", []) if not item.get("is_duplicate")]
        sample_size = len(comments)
        if sample_size < 2:
            return []

        candidates: list[tuple[str, str, list[dict[str, Any]]]] = []
        for field, card_type in [
            ("painpoint", "risk_explanation"),
            ("positive_attribution", "opportunity_amplification"),
        ]:
            grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
            for comment in comments:
                classification = comment.get(field) or {}
                category = str(classification.get("category") or "").strip()
                if category:
                    grouped[category].append(comment)
            candidates.extend((category, card_type, group) for category, group in grouped.items())

        clustered: dict[str, list[dict[str, Any]]] = defaultdict(list)
        cluster_names = {
            item.get("cluster_id"): item.get("cluster_name")
            for item in result.get("clusters", [])
            if not item.get("is_noise")
        }
        for comment in comments:
            cluster_name = cluster_names.get(comment.get("cluster_id"))
            if cluster_name:
                clustered[str(cluster_name)].append(comment)
        candidates.extend((name, "topic_explanation", group) for name, group in clustered.items())

        candidates.sort(key=lambda item: len(item[2]), reverse=True)
        cards: list[dict[str, Any]] = []
        used_signatures: set[tuple[str, ...]] = set()
        for category, card_type, group in candidates:
            if len(group) < 2:
                continue
            ordered = sorted(group, key=lambda item: int(item.get("like_count") or 0), reverse=True)
            evidence = [
                {
                    "comment_id": str(item.get("id")),
                    "content": item.get("cleaned_content") or item.get("content") or "",
                    "source_url": item.get("source_url") or "",
                    "like_count": int(item.get("like_count") or 0),
                }
                for item in ordered[:3]
            ]
            signature = tuple(item["comment_id"] for item in evidence)
            if signature in used_signatures:
                continue
            used_signatures.add(signature)
            ratio = len(group) / sample_size
            confidence, confidence_reason = self._confidence(len(group), sample_size, ratio)
            cards.append(
                {
                    "title": self._title(category, card_type),
                    "card_type": card_type,
                    "evidence_comment_ids": [item["comment_id"] for item in evidence],
                    "evidence_comments": evidence,
                    "evidence_count": len(group),
                    "sample_size": sample_size,
                    "affected_ratio": round(ratio, 4),
                    "confidence": confidence,
                    "confidence_reason": confidence_reason,
                    "suggested_actions": self._actions(category, card_type),
                    "expected_impact": self._impact(card_type),
                    "ab_test_design": self._ab_test(category, card_type, sample_size),
                }
            )
            if len(cards) >= 4:
                break
        return cards

    @staticmethod
    def _confidence(evidence_count: int, sample_size: int, ratio: float) -> tuple[str, str]:
        if sample_size < 100:
            return "low", f"样本量仅 {sample_size} 条，小于 100；证据 {evidence_count} 条，占比 {ratio:.1%}。"
        if evidence_count >= 12 and ratio >= 0.12:
            return "high", f"证据 {evidence_count} 条，占 {sample_size} 条样本的 {ratio:.1%}，覆盖稳定。"
        if evidence_count >= 5:
            return "medium", f"证据 {evidence_count} 条，占比 {ratio:.1%}，建议继续补充样本验证。"
        return "low", f"只有 {evidence_count} 条证据，占比 {ratio:.1%}，结论仅供探索。"

    @staticmethod
    def _title(category: str, card_type: str) -> str:
        if card_type == "risk_explanation":
            return f"用事实拆解「{category}」争议"
        if card_type == "opportunity_amplification":
            return f"放大「{category}」认可点"
        return f"围绕「{category.split('｜', 1)[0]}」制作深度解读"

    @staticmethod
    def _actions(category: str, card_type: str) -> list[str]:
        if card_type == "risk_explanation":
            return [
                f"整理与「{category}」直接相关的比赛回合、技术统计和官方说明。",
                "将事实、球迷观点和仍无法确认的信息分栏呈现。",
                "在标题和摘要中避免把抽样评论写成全体球迷结论。",
            ]
        if card_type == "opportunity_amplification":
            return [
                f"围绕「{category}」制作球员表现或球队战术拆解。",
                "引用高赞代表评论，同时附上对应技术统计和比赛节点。",
                "补充不同立场评论，避免只展示单一阵营。",
            ]
        return [
            f"以「{category.split('｜', 1)[0]}」为主线组织比赛复盘。",
            "按观点、证据和反方意见三个层次编排内容。",
            "在结尾列出下一场可继续验证的数据指标。",
        ]

    @staticmethod
    def _impact(card_type: str) -> str:
        if card_type == "risk_explanation":
            return "降低争议内容中的事实混淆，提高报告可解释性。"
        if card_type == "opportunity_amplification":
            return "提升高认可主题的内容相关性和读者互动。"
        return "让分散评论形成可阅读、可验证的比赛主题脉络。"

    @staticmethod
    def _ab_test(category: str, card_type: str, sample_size: int) -> dict[str, Any]:
        return {
            "hypothesis": f"使用证据导向的「{category}」拆解，比普通赛后摘要获得更高的有效阅读和理性互动。",
            "control": "发布常规赛后概述，只呈现结论。",
            "variant": "发布观点 + 原评论证据 + 技术统计/官方上下文的结构化拆解。",
            "primary_metric": "报告完整阅读率",
            "guardrail_metrics": ["负面举报率", "事实更正次数", "评论区无关争论占比"],
            "sample_size_note": f"当前分析样本为 {sample_size} 条；实验流量和周期需在发布渠道中另行估算。",
            "source_type": card_type,
        }
