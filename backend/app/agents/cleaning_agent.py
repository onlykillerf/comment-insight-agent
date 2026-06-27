from __future__ import annotations

import re


class DataCleaningAgent:
    """Clean low-quality text while preserving short emotional comments."""

    ad_patterns = [r"加微", r"VX", r"兼职", r"开户链接", r"http[s]?://\S+", r"点点关注", r"点点赞", r"多多转发"]
    flood_texts = {"666", "111", "顶", "路过", "签到"}
    emoji_map = {
        "👍": " 好评 ",
        "❤️": " 喜欢 ",
        "🔥": " 火热 ",
        "😡": " 生气 ",
        "😭": " 难受 ",
    }

    def run(self, comments: list[dict]) -> list[dict]:
        """Return cleaned comments with quality score and language."""

        cleaned: list[dict] = []
        for comment in comments:
            content = str(comment.get("analysis_content") or comment.get("content") or "").strip()
            cleaned_text = self.normalize(content)
            if not cleaned_text:
                continue
            quality_score = self.quality_score(cleaned_text)
            if quality_score <= 0.2:
                continue
            item = dict(comment)
            item.update(
                {
                    "cleaned_content": cleaned_text,
                    "language": self.detect_language(cleaned_text),
                    "quality_score": quality_score,
                    "is_duplicate": False,
                    "duplicate_group_id": None,
                }
            )
            cleaned.append(item)
        return cleaned

    def normalize(self, text: str) -> str:
        """Normalize whitespace, common emoji and noisy characters."""

        for emoji, replacement in self.emoji_map.items():
            text = text.replace(emoji, replacement)
        text = re.sub(r"@\S+", " ", text)
        text = re.sub(r"(^|\s)(作者|置顶评论|回复|赞)(\s|$)", " ", text)
        text = re.sub(r"展开\s*\d+\s*条回复", " ", text)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"[^\w\u4e00-\u9fff，。！？、,.!?：:；;（）()\-\s]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def quality_score(self, text: str) -> float:
        """Score text quality, filtering ads and meaningless flooding."""

        compact = re.sub(r"\s+", "", text).lower()
        if compact in self.flood_texts:
            return 0.0
        if any(re.search(pattern, text, re.IGNORECASE) for pattern in self.ad_patterns):
            return 0.1
        if len(compact) <= 1:
            return 0.0
        if len(compact) <= 4 and compact not in {"太爽了", "真恶心", "真香", "好玩", "难受"}:
            return 0.45
        return min(1.0, 0.55 + len(compact) / 80)

    def detect_language(self, text: str) -> str:
        """Detect Chinese vs English for the MVP."""

        chinese_count = len(re.findall(r"[\u4e00-\u9fff]", text))
        ascii_count = len(re.findall(r"[A-Za-z]", text))
        return "zh" if chinese_count >= ascii_count else "en"
