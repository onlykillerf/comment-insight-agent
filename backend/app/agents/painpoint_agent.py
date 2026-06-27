from __future__ import annotations

from app.taxonomies import classify_label


class PainPointAgent:
    """Analyze negative comment categories using domain taxonomy."""

    def run(self, comments: list[dict], domain: str = "game") -> list[dict]:
        """Attach pain point for negative comments."""

        for comment in comments:
            score = comment.get("sentiment", {}).get("score", 0)
            if score >= -0.1:
                continue
            category, term, confidence = classify_label(comment.get("cleaned_content", ""), domain, "negative")
            comment["painpoint"] = {
                "category": category,
                "confidence": confidence,
                "reason": f"命中领域词：{term}" if term else "负向表达明显，归入领域默认负向标签。",
            }
        return comments
