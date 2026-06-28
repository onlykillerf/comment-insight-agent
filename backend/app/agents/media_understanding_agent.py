from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

from app.services.vision_service import SiliconFlowVisionService


class MediaUnderstandingAgent:
    """Analyze informative images from source posts and news context, never replies."""

    _official_domains = {
        "nba.com",
        "fifa.com",
        "uefa.com",
        "the-afc.com",
        "thecfa.cn",
        "cbaleague.com",
    }
    _authority_terms = {
        "官方",
        "官网",
        "流言板",
        "裁判报告",
        "联盟公告",
        "球队公告",
        "数据统计",
        "技术统计",
    }
    _information_terms = {
        "数据",
        "统计",
        "正负值",
        "命中率",
        "投篮",
        "三分",
        "篮板",
        "助攻",
        "抢断",
        "盖帽",
        "失误",
        "比分",
        "效率",
        "轮换",
        "阵容",
        "伤病",
        "判罚",
        "裁判",
        "战术",
        "热区",
        "薪资",
    }

    def __init__(self, service: SiliconFlowVisionService | None = None) -> None:
        self.service = service or SiliconFlowVisionService()

    def run(
        self,
        comments: list[dict[str, Any]],
        news_context_items: list[dict[str, Any]],
        config: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Return bounded, source-level visual evidence for the insight pipeline."""

        candidates = self._thread_candidates(comments, config) + self._news_candidates(news_context_items, config)
        candidates = [candidate for candidate in candidates if candidate["information_score"] >= 2]
        authority_rank = {"official": 4, "official_reference": 3, "editorial": 2, "community_data": 1}
        candidates.sort(
            key=lambda item: (
                authority_rank.get(item["authority_level"], 0),
                item["information_score"],
            ),
            reverse=True,
        )

        enabled = bool(config.get("enable_image_analysis", True))
        remaining = max(0, int(config.get("max_image_comments") or 0))
        results: list[dict[str, Any]] = []
        seen_images: set[str] = set()
        for candidate in candidates:
            for index, image_url in enumerate(candidate["image_urls"]):
                if image_url in seen_images:
                    continue
                seen_images.add(image_url)
                media_item = {
                    **candidate,
                    "source_id": f"{candidate['source_id']}-image-{index + 1}",
                    "image_urls": [image_url],
                }
                if not enabled:
                    analysis = {"status": "disabled", "model": self.service.settings.siliconflow_vision_model}
                elif remaining <= 0:
                    analysis = {"status": "skipped_limit", "model": self.service.settings.siliconflow_vision_model}
                else:
                    analysis = self.service.analyze_context_media(media_item, config)
                    remaining -= 1
                included = (
                    analysis.get("status") == "completed"
                    and analysis.get("relevance") in {"high", "medium"}
                    and analysis.get("information_value") in {"high", "medium"}
                    and self._has_visual_information(analysis)
                )
                exclusion_reason = ""
                if analysis.get("status") == "completed" and not included:
                    if analysis.get("information_value") == "low":
                        exclusion_reason = "图片信息量低"
                    elif not self._has_visual_information(analysis):
                        exclusion_reason = "OCR 未提供足够的可见数据或报告信号"
                    else:
                        exclusion_reason = "与当前比赛相关性不足"
                results.append(
                    {
                        **media_item,
                        **analysis,
                        "included_in_summary": included,
                        "exclusion_reason": exclusion_reason,
                    }
                )
        return results

    def _thread_candidates(
        self, comments: list[dict[str, Any]], config: dict[str, Any]
    ) -> list[dict[str, Any]]:
        candidates: list[dict[str, Any]] = []
        seen_threads: set[str] = set()
        for comment in comments:
            metadata = comment.get("metadata") or {}
            thread_id = str(metadata.get("thread_id") or comment.get("source_url") or "")
            if not thread_id or thread_id in seen_threads:
                continue
            seen_threads.add(thread_id)
            images = self._prioritize_images(metadata.get("thread_image_urls") or [])
            if not images:
                continue
            title = str(metadata.get("thread_title") or comment.get("topic") or "")
            summary = str(metadata.get("thread_excerpt") or "")
            score, authority, reasons = self._score_source(
                title=title,
                summary=summary,
                source_url=str(comment.get("source_url") or ""),
                source_kind="hupu_thread",
                config=config,
            )
            candidates.append(
                {
                    "source_id": f"hupu-thread-{thread_id}",
                    "source_kind": "hupu_thread",
                    "title": title,
                    "text_context": summary[:1800],
                    "source_url": comment.get("source_url", ""),
                    "image_urls": images,
                    "authority_level": authority,
                    "information_score": score,
                    "selection_reasons": reasons,
                }
            )
        return candidates

    def _news_candidates(
        self, items: list[dict[str, Any]], config: dict[str, Any]
    ) -> list[dict[str, Any]]:
        candidates: list[dict[str, Any]] = []
        for index, item in enumerate(items):
            if item.get("status") == "error":
                continue
            images = self._prioritize_images(item.get("image_urls") or [])
            if not images:
                continue
            title = str(item.get("title") or "")
            summary = str(item.get("summary") or "")
            source_url = str(item.get("url") or "")
            score, authority, reasons = self._score_source(
                title=title,
                summary=summary,
                source_url=source_url,
                source_kind="news",
                config=config,
            )
            candidates.append(
                {
                    "source_id": f"news-{index}-{source_url}",
                    "source_kind": "news",
                    "title": title,
                    "text_context": summary[:1800],
                    "source_url": source_url,
                    "image_urls": images,
                    "authority_level": authority,
                    "information_score": score,
                    "selection_reasons": reasons,
                }
            )
        return candidates

    def _score_source(
        self,
        title: str,
        summary: str,
        source_url: str,
        source_kind: str,
        config: dict[str, Any],
    ) -> tuple[int, str, list[str]]:
        text = f"{title} {summary}"
        reasons: list[str] = []
        score = 0
        authority_hits = sorted(term for term in self._authority_terms if term in text)
        information_hits = sorted(term for term in self._information_terms if term in text)
        host = (urlparse(source_url).hostname or "").lower()
        official_domain = any(host == domain or host.endswith(f".{domain}") for domain in self._official_domains)

        if official_domain:
            score += 4
            reasons.append("官方体育域名")
        if authority_hits:
            score += 3
            reasons.append(f"权威来源信号：{'、'.join(authority_hits[:3])}")
        if information_hits:
            score += min(4, len(information_hits))
            reasons.append(f"数据/赛事信号：{'、'.join(information_hits[:4])}")
        match_terms = [
            str(config.get(key) or "")
            for key in ["home_team", "away_team", "match_name"]
            if config.get(key)
        ]
        if any(term in text for term in match_terms):
            score += 1
            reasons.append("匹配当前比赛或球队")

        if official_domain:
            authority = "official"
        elif any(term in text for term in {"官方", "官网", "裁判报告", "联盟公告"}):
            authority = "official_reference"
        elif source_kind == "news" or "流言板" in text:
            authority = "editorial"
        else:
            authority = "community_data"
        return score, authority, reasons

    @staticmethod
    def _prioritize_images(values: list[str]) -> list[str]:
        urls = [
            str(value)
            for value in values
            if str(value).startswith(("https://", "http://")) and ".gif" not in str(value).lower()
        ]

        def score(url: str) -> tuple[int, int]:
            lowered = url.lower()
            information_hint = int(".png" in lowered) * 3 + int("news-editor" in lowered) * 2
            return information_hint, len(url)

        ranked = sorted(dict.fromkeys(urls), key=score, reverse=True)
        likely_information_graphics = [url for url in ranked if score(url)[0] > 0]
        return (likely_information_graphics or ranked[:1])[:4]

    @staticmethod
    def _has_visual_information(analysis: dict[str, Any]) -> bool:
        ocr = str(analysis.get("ocr_text") or "").strip()
        if len(ocr) < 6:
            return False
        lowered = ocr.lower()
        live_period = re.search(r"\b(?:1st|2nd|3rd|4th|q[1-4])\b", lowered) or re.search(
            r"第[一二三四1-4]节", ocr
        )
        live_clock = re.search(r"\b\d{1,2}:\d{2}\b", ocr)
        if live_period and live_clock:
            return False
        numbers = re.findall(r"\d+(?:\.\d+)?", ocr)
        signal_terms = {
            "pts",
            "reb",
            "ast",
            "stl",
            "blk",
            "fg",
            "3pt",
            "score",
            "final",
            "injury",
            "out",
            "questionable",
            "referee",
            "official",
            "report",
            "得分",
            "篮板",
            "助攻",
            "抢断",
            "盖帽",
            "命中率",
            "伤病",
            "缺阵",
            "裁判",
            "报告",
        }
        return len(numbers) >= 2 or any(term in lowered for term in signal_terms)
