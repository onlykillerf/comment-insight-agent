from __future__ import annotations


class SentimentAgent:
    """Classify comments into five sentiment labels with a score from -1 to 1."""

    positive_terms = {
        "爽": 0.35,
        "喜欢": 0.3,
        "漂亮": 0.25,
        "舒服": 0.25,
        "强": 0.22,
        "好玩": 0.35,
        "创意": 0.22,
        "燃": 0.3,
        "fun": 0.25,
        "great": 0.3,
        "insane": 0.2,
        "球王": 0.28,
        "老板": 0.22,
        "高光": 0.25,
        "破门": 0.25,
        "登顶": 0.25,
        "加冕": 0.25,
        "牛": 0.28,
        "太强": 0.28,
        "流畅": 0.22,
        "不错": 0.2,
        "期待": 0.22,
        "看好": 0.24,
        "谨慎看好": 0.16,
        "真香": 0.28,
        "赚": 0.22,
        "不亏": 0.2,
        "值": 0.18,
        "捡漏": 0.24,
        "性价比": 0.22,
        "大年": 0.18,
        "天赋": 0.18,
        "潜力": 0.18,
        "有谱": 0.24,
        "补强": 0.2,
        "适配": 0.16,
        "上限最高": 0.24,
        "身体天赋": 0.18,
        "身体模板": 0.18,
        "成长空间": 0.2,
        "技术稀缺": 0.22,
        "培养环境": 0.16,
        "适配球队": 0.2,
        "国际球员": 0.16,
        "话题热度": 0.14,
        "投射技术强": 0.22,
        "基本功较好": 0.18,
        "纪录": 0.2,
        "记录": 0.2,
        "价值": 0.16,
    }
    negative_terms = {
        "烦": -0.35,
        "广告": -0.18,
        "强制": -0.32,
        "卡顿": -0.35,
        "发热": -0.2,
        "离谱": -0.28,
        "压力": -0.2,
        "不透明": -0.3,
        "不平衡": -0.32,
        "打断": -0.3,
        "气绝": -0.35,
        "不防": -0.22,
        "防不住": -0.22,
        "遗憾": -0.2,
        "错失": -0.2,
        "亏": -0.25,
        "看不懂": -0.22,
        "疯了": -0.2,
        "浪费": -0.28,
        "水货": -0.35,
        "上限低": -0.28,
        "不值": -0.25,
        "风险": -0.18,
        "差": -0.16,
        "错了": -0.18,
        "走不远": -0.24,
        "打不出来": -0.26,
        "刺头": -0.22,
        "球商": -0.12,
        "视野差": -0.24,
        "不明白": -0.18,
        "不理解": -0.18,
        "质疑": -0.18,
        "反对": -0.24,
        "别选": -0.3,
        "不要": -0.22,
        "顺位过高": -0.28,
        "选高了": -0.24,
        "对抗差": -0.24,
        "太瘦": -0.2,
        "移动慢": -0.22,
        "横移慢": -0.22,
        "投篮不稳": -0.24,
        "投射差": -0.24,
        "防守差": -0.22,
        "伤病": -0.24,
        "太毛坯": -0.22,
        "周期太长": -0.22,
        "吹过了": -0.2,
        "含金量": -0.16,
        "争议": -0.16,
        "unfair": -0.35,
        "forced": -0.3,
        "too many": -0.3,
    }

    def run(self, comments: list[dict]) -> list[dict]:
        """Attach sentiment result to comments."""

        for comment in comments:
            score = self.score(comment["cleaned_content"])
            comment["sentiment"] = {
                "label": self.label(score),
                "score": score,
                "confidence": min(0.95, 0.55 + abs(score) * 0.4),
            }
        return comments

    def score(self, text: str) -> float:
        """Calculate rule-based sentiment score."""

        lower = text.lower()
        value = 0.0
        for term, weight in self.positive_terms.items():
            if term.lower() in lower:
                value += weight
        for term, weight in self.negative_terms.items():
            if term.lower() in lower:
                value += weight
        return max(-1.0, min(1.0, round(value, 3)))

    def label(self, score: float) -> str:
        """Map numeric score to a five-level label."""

        if score >= 0.55:
            return "strong_positive"
        if score >= 0.15:
            return "positive"
        if score <= -0.55:
            return "strong_negative"
        if score <= -0.15:
            return "negative"
        return "neutral"
