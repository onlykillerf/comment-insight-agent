from __future__ import annotations


class RepresentativeSamplerAgent:
    """Sample representative comments from each cluster."""

    def run(self, comments: list[dict], clusters: list[dict], per_cluster: int = 3) -> list[dict]:
        """Return high-signal comments for every cluster."""

        representatives: list[dict] = []
        for cluster in clusters:
            cluster_comments = [
                comment for comment in comments if comment.get("cluster_id") == cluster["cluster_id"] and not comment.get("is_duplicate")
            ]
            ranked = sorted(cluster_comments, key=self._score, reverse=True)
            for comment in ranked[:per_cluster]:
                representatives.append(
                    {
                        "cluster_id": cluster["cluster_id"],
                        "comment_id": comment["id"],
                        "content": comment["cleaned_content"],
                        "reason": "靠近主题、高点赞或情绪表达明确。",
                    }
                )
        return representatives

    def _score(self, comment: dict) -> float:
        sentiment_strength = abs(comment.get("sentiment", {}).get("score", 0))
        clarity = min(1.0, len(comment.get("cleaned_content", "")) / 80)
        return float(comment.get("like_count") or 0) * 0.08 + sentiment_strength + clarity

