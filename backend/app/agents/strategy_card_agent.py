from __future__ import annotations

from typing import Any


class StrategyCardAgent:
    """Generate evidence-grounded strategy cards from structured analysis only."""

    def run(self, context: dict[str, Any]) -> list[dict[str, Any]]:
        """Return strategy cards with real evidence comments and calibrated confidence."""

        domain = context.get("config", {}).get("domain", "game")
        quality = context.get("data_quality_report") or {}
        sample_size = int(quality.get("dedup_count") or len([c for c in context.get("comments", []) if not c.get("is_duplicate")]))
        cards: list[dict[str, Any]] = []

        for item in context.get("painpoints", [])[:3]:
            card = self._build_card(item, domain, sample_size, polarity="negative")
            if card:
                cards.append(card)
        for item in context.get("positive_attributions", [])[:2]:
            card = self._build_card(item, domain, sample_size, polarity="positive")
            if card:
                cards.append(card)
        return cards[:5]

    def _build_card(self, item: dict[str, Any], domain: str, sample_size: int, polarity: str) -> dict[str, Any] | None:
        examples = [text for text in item.get("examples", []) if str(text).strip()]
        evidence_count = int(item.get("count") or len(examples))
        if len(examples) < 2 or evidence_count < 2:
            return None

        category = item["category"]
        ratio = evidence_count / max(1, sample_size)
        sentiment_strength = self._sentiment_strength(item.get("sentiment_distribution", {}), evidence_count)
        confidence, confidence_reason = self._confidence(evidence_count, sample_size, ratio, sentiment_strength)
        priority = self._priority(ratio, confidence, polarity)

        if polarity == "negative":
            title = f"Explain and monitor `{category}`"
            card_type = "risk_explanation"
            problem_or_opportunity = (
                f"{evidence_count} real comments mention `{category}`, covering {ratio:.1%} of the deduplicated sample. "
                "Treat this as an evidence-backed risk theme, not a universal audience conclusion."
            )
            actions = self._negative_actions(category, domain)
            expected_impact = self._negative_impact(domain)
        else:
            title = f"Amplify `{category}`"
            card_type = "opportunity_amplification"
            problem_or_opportunity = (
                f"{evidence_count} real comments support `{category}`, covering {ratio:.1%} of the deduplicated sample. "
                "This can become a content angle, product message, or follow-up analysis topic."
            )
            actions = self._positive_actions(category, domain)
            expected_impact = self._positive_impact(domain)

        return {
            "title": title,
            "type": card_type,
            "priority": priority,
            "problem_or_opportunity": problem_or_opportunity,
            "evidence_comments": examples[:3],
            "evidence_count": evidence_count,
            "sample_size": sample_size,
            "confidence": confidence,
            "confidence_reason": confidence_reason,
            "affected_ratio": f"{ratio:.1%}",
            "suggested_actions": actions,
            "expected_impact": expected_impact,
            "ab_test_design": self._ab_test(category, domain, polarity),
        }

    def _confidence(self, evidence_count: int, sample_size: int, ratio: float, sentiment_strength: float) -> tuple[str, str]:
        reasons: list[str] = []
        if sample_size < 100:
            reasons.append("sample_size < 100, so this card is downgraded to low confidence for demo/triage only. ")
        if evidence_count < 3:
            reasons.append("evidence_count is below 3, so the theme needs more validation. ")
        if ratio < 0.03:
            reasons.append("affected_ratio is below 3%, so the theme is narrow in the current sample. ")
        if reasons:
            return "low", "".join(reasons).strip()
        if evidence_count >= 20 and ratio >= 0.15 and sentiment_strength >= 0.35:
            return "high", "Evidence volume, affected_ratio, and sentiment concentration are all strong."
        if evidence_count >= 5 and ratio >= 0.05:
            return "medium", "Evidence comes from real classified comments, but the sample or sentiment concentration is not yet strong enough for high confidence."
        return "low", "Evidence is real but still sparse; expand the sample before treating this as a stable pattern."

    def _priority(self, ratio: float, confidence: str, polarity: str) -> str:
        if polarity == "negative" and ratio >= 0.15 and confidence != "low":
            return "high"
        if ratio >= 0.08:
            return "medium"
        return "low"

    def _sentiment_strength(self, distribution: dict[str, int], evidence_count: int) -> float:
        if not distribution or evidence_count <= 0:
            return 0.0
        polar = distribution.get("positive", 0) + distribution.get("strong_positive", 0)
        polar += distribution.get("negative", 0) + distribution.get("strong_negative", 0)
        return round(polar / max(1, evidence_count), 4)

    def _negative_actions(self, category: str, domain: str) -> list[str]:
        if domain == "nba_draft":
            return [
                f"Publish an explainer around `{category}` with comment evidence, scouting data, game clips, and counterexamples.",
                "Separate ceiling comps, floor risks, and current skills when discussing player templates.",
                "Add team-fit analysis: pick range, roster need, development timeline, and risk tolerance.",
            ]
        if domain == "iaa_game":
            return [
                f"Run a focused product experiment for `{category}` and segment new vs returning users.",
                "Map evidence comments to exact journey steps: onboarding, failure screen, ad trigger, reward claim, or match result.",
                "Track retention, ad completion, negative review rate, and session length before and after the change.",
            ]
        if domain == "news":
            return [
                f"Turn `{category}` into a clarification card with timeline, source links, and unresolved questions.",
                "Separate factual disputes, stance conflict, and emotional escalation before responding.",
                "Monitor high-like skeptical comments and update the public explanation when new facts appear.",
            ]
        return [
            f"Review the source posts and high-like comments behind `{category}`.",
            "Separate jokes, rational criticism, and attack language before choosing an intervention.",
            "Track the theme by platform and time window after the next sample refresh.",
        ]

    def _positive_actions(self, category: str, domain: str) -> list[str]:
        if domain == "nba_draft":
            return [
                f"Use `{category}` as a recurring draft content angle with player templates, pick value, and team-fit breakdowns.",
                "Quote representative comments in the hook, then support them with stats and clip evidence.",
                "Compare the same label across multiple prospects to build a repeatable draft board series.",
            ]
        if domain == "iaa_game":
            return [
                f"Turn `{category}` into store-page copy, short-video hooks, or onboarding proof points.",
                "Keep the original user wording, but validate it with retention and ad-engagement metrics.",
                "A/B test this message against generic fun/relaxation copy.",
            ]
        if domain == "news":
            return [
                f"Use `{category}` to create a concise information card that reduces repeated questions.",
                "Quote representative comments only when they are backed by source material.",
                "Compare the response under different headline framings to avoid escalating stance conflict.",
            ]
        return [
            f"Convert `{category}` evidence into reusable content hooks and product messages.",
            "Preserve user language, then add data or examples to make the claim credible.",
            "Measure lift in CTR, share rate, and positive comment ratio.",
        ]

    def _negative_impact(self, domain: str) -> str:
        if domain == "nba_draft":
            return "Reduce misread draft narratives by turning controversy into explainable, evidence-backed content."
        if domain == "iaa_game":
            return "Reduce review risk and retention loss by tying pain points to concrete product experiments."
        if domain == "news":
            return "Lower rumor spread and stance escalation by clarifying facts and uncertainty boundaries."
        return "Identify controversy earlier and avoid overreacting to unsupported single-comment signals."

    def _positive_impact(self, domain: str) -> str:
        if domain == "nba_draft":
            return "Increase draft content depth and repeatable topic density while preserving comment evidence."
        if domain == "iaa_game":
            return "Convert authentic praise into acquisition copy, onboarding proof, and retention experiments."
        if domain == "news":
            return "Use audience-recognized information value to improve clarity and trust."
        return "Turn real positive language into more stable content and product messaging."

    def _ab_test(self, category: str, domain: str, polarity: str) -> dict[str, Any]:
        if domain == "nba_draft":
            return {
                "control_group": "Generic draft news headline and summary.",
                "experiment_group": f"`{category}` evidence-led explainer with representative comments and data.",
                "metrics": ["CTR", "read_completion", "save_rate", "positive_comment_ratio", "high_like_skeptical_comments"],
            }
        if domain == "iaa_game":
            return {
                "control_group": "Current product flow or generic ad/reward copy.",
                "experiment_group": f"Flow or copy adjusted for `{category}` with evidence-backed hypothesis.",
                "metrics": ["D1_retention", "session_length", "ad_completion_rate", "negative_review_rate"],
            }
        if domain == "news":
            return {
                "control_group": "Standard article headline and comment moderation flow.",
                "experiment_group": f"Clarification-first framing around `{category}` with source timeline.",
                "metrics": ["read_completion", "share_rate", "skeptical_comment_ratio", "report_rate"],
            }
        return {
            "control_group": "Current content or product expression.",
            "experiment_group": f"Expression emphasizing `{category}` and citing representative comments.",
            "metrics": ["CTR", "interaction_rate", "positive_comment_ratio", "negative_comment_ratio"],
        }
