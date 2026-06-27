from __future__ import annotations

from app.taxonomies import classify_label


class PositiveAttributionAgent:
    """Analyze why positive comments are positive using domain taxonomy."""

    def run(self, comments: list[dict], domain: str = "game") -> list[dict]:
        """Attach positive attribution for positive comments."""

        for comment in comments:
            score = comment.get("sentiment", {}).get("score", 0)
            if score <= 0.1:
                continue
            category, term, confidence = classify_label(comment.get("cleaned_content", ""), domain, "positive")
            comment["positive_attribution"] = {
                "category": category,
                "confidence": confidence,
                "reason": f"命中领域词：{term}" if term else "正向表达明显，归入领域默认正向标签。",
            }
        return comments
