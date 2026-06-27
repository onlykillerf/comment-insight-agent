from __future__ import annotations

import math
from collections import Counter, defaultdict
from typing import Any

from app.services.chinese_nlp import GENERAL_DOMAIN_TERMS, tokenize
from app.taxonomies import classify_stance, get_taxonomy


class ClusteringAgent:
    """Cluster comments with HDBSCAN first, then KMeans or rule fallback."""

    def run(self, comments: list[dict], method: str = "auto", domain: str = "game") -> list[dict[str, Any]]:
        """Return cluster summaries and assign cluster_id on comments."""

        non_duplicate = [comment for comment in comments if not comment.get("is_duplicate")]
        if not non_duplicate:
            return []
        if len(non_duplicate) >= 30:
            clusters = self._hdbscan(non_duplicate, domain)
            if clusters:
                return clusters
        if len(non_duplicate) >= 12:
            clusters = self._kmeans(non_duplicate, domain)
            if clusters:
                return clusters
        return self._rule_groups(non_duplicate, domain, method="rules")

    def _hdbscan(self, comments: list[dict], domain: str) -> list[dict[str, Any]]:
        try:
            import hdbscan  # type: ignore
        except Exception:
            return []

        vectors = self._vectors(comments)
        if not vectors:
            return []
        min_cluster_size = max(4, int(math.sqrt(len(comments))))
        labels = hdbscan.HDBSCAN(min_cluster_size=min_cluster_size).fit_predict(vectors)
        return self._clusters_from_labels(comments, labels, domain, method="hdbscan")

    def _kmeans(self, comments: list[dict], domain: str) -> list[dict[str, Any]]:
        try:
            from sklearn.cluster import KMeans
        except Exception:
            return []

        signal_comments = [comment for comment in comments if not self._looks_like_noise(comment, domain)]
        noise_comments = [comment for comment in comments if self._looks_like_noise(comment, domain)]
        if len(signal_comments) < 2:
            return []

        vectors = self._vectors(signal_comments)
        if not vectors:
            return []
        cluster_count = min(6, max(2, int(math.sqrt(len(signal_comments)))))
        if len(signal_comments) <= cluster_count:
            return []
        model = KMeans(n_clusters=cluster_count, random_state=42, n_init="auto")
        labels = model.fit_predict(vectors)
        label_by_object = {id(comment): int(label) for comment, label in zip(signal_comments, labels)}
        for comment in noise_comments:
            label_by_object[id(comment)] = -1
        combined_labels = [label_by_object[id(comment)] for comment in comments]
        return self._clusters_from_labels(comments, combined_labels, domain, method="kmeans")

    def _rule_groups(self, comments: list[dict], domain: str, method: str) -> list[dict[str, Any]]:
        groups: dict[str, list[dict]] = defaultdict(list)
        for comment in comments:
            groups[self._topic_key(comment, domain)].append(comment)
        labels = []
        ordered_keys = sorted(groups, key=lambda key: (key == "__noise__", -len(groups[key]), key))
        key_to_id = {key: (-1 if key == "__noise__" else index) for index, key in enumerate(k for k in ordered_keys if k != "__noise__")}
        if "__noise__" in groups:
            key_to_id["__noise__"] = -1
        label_by_id: dict[str, int] = {}
        for key, group in groups.items():
            for comment in group:
                label_by_id[str(id(comment))] = key_to_id[key]
        for comment in comments:
            labels.append(label_by_id[str(id(comment))])
        return self._clusters_from_labels(comments, labels, domain, method=method)

    def _clusters_from_labels(
        self, comments: list[dict], labels: list[int], domain: str, method: str
    ) -> list[dict[str, Any]]:
        grouped: dict[int, list[dict]] = defaultdict(list)
        for comment, label in zip(comments, labels):
            label = int(label)
            grouped[label].append(comment)
            comment["cluster_id"] = label

        total = len(comments)
        clusters: list[dict[str, Any]] = []
        ordered = sorted(grouped.items(), key=lambda item: (item[0] == -1, -len(item[1])))
        next_id = 0
        id_map: dict[int, int] = {}
        for label, group in ordered:
            if label == -1:
                id_map[label] = -1
            else:
                id_map[label] = next_id
                next_id += 1

        for original_label, group in ordered:
            cluster_id = id_map[original_label]
            for comment in group:
                comment["cluster_id"] = cluster_id
            sentiment_distribution = Counter(item.get("sentiment", {}).get("label", "neutral") for item in group)
            keywords = self._top_keywords(group, domain)
            representatives = self._representative_texts(group)
            is_noise = original_label == -1 or self._looks_like_noise_group(group, domain)
            base_name = self._base_name(group, domain, is_noise)
            clusters.append(
                {
                    "cluster_id": cluster_id,
                    "cluster_name": self._cluster_name(base_name, keywords, representatives, sentiment_distribution, is_noise),
                    "cluster_size": len(group),
                    "cluster_ratio": round(len(group) / total, 4),
                    "top_keywords": keywords,
                    "sentiment_distribution": dict(sentiment_distribution),
                    "method": method,
                    "is_noise": is_noise,
                    "representative_comments": representatives,
                }
            )
        return clusters

    def _topic_key(self, comment: dict, domain: str) -> str:
        if self._looks_like_noise(comment, domain):
            return "__noise__"
        if comment.get("painpoint"):
            return comment["painpoint"]["category"]
        if comment.get("positive_attribution"):
            return comment["positive_attribution"]["category"]
        stance, _, _ = classify_stance(comment.get("cleaned_content", ""), domain)
        return "信息补充/中性讨论" if stance in {"信息补充", "无关"} else f"{stance}讨论"

    def _base_name(self, comments: list[dict], domain: str, is_noise: bool) -> str:
        if is_noise:
            return "噪声/低信息评论"
        counter: Counter[str] = Counter()
        for comment in comments:
            if comment.get("painpoint"):
                counter[comment["painpoint"]["category"]] += 1
            elif comment.get("positive_attribution"):
                counter[comment["positive_attribution"]["category"]] += 1
        if counter:
            return counter.most_common(1)[0][0]
        stance_counter = Counter(classify_stance(comment.get("cleaned_content", ""), domain)[0] for comment in comments)
        stance = stance_counter.most_common(1)[0][0]
        return "信息补充/中性讨论" if stance == "无关" else f"{stance}讨论"

    def _cluster_name(
        self,
        base_name: str,
        keywords: list[str],
        representatives: list[str],
        sentiment_distribution: Counter[str],
        is_noise: bool,
    ) -> str:
        if is_noise:
            return base_name
        top_sentiment = sentiment_distribution.most_common(1)[0][0] if sentiment_distribution else "neutral"
        keyword_part = "、".join(keywords[:3]) if keywords else "无明显关键词"
        evidence_hint = representatives[0][:18] if representatives else ""
        suffix = f"｜{keyword_part}｜{top_sentiment}"
        if evidence_hint:
            suffix += f"｜例：{evidence_hint}"
        return f"{base_name}{suffix}"[:160]

    def _top_keywords(self, comments: list[dict], domain: str) -> list[str]:
        counter: Counter[str] = Counter()
        for comment in comments:
            counter.update(tokenize(comment.get("cleaned_content", ""), domain))
        return [word for word, _ in counter.most_common(6)]

    def _representative_texts(self, comments: list[dict]) -> list[str]:
        ranked = sorted(
            comments,
            key=lambda comment: (
                int(comment.get("like_count") or 0),
                abs(float(comment.get("sentiment", {}).get("score") or 0)),
                len(comment.get("cleaned_content", "")),
            ),
            reverse=True,
        )
        return [comment.get("cleaned_content", "") for comment in ranked[:3] if comment.get("cleaned_content")]

    def _vectors(self, comments: list[dict]) -> list[list[float]]:
        vectors = [comment.get("embedding") for comment in comments]
        if not vectors or any(not isinstance(vector, list) or not vector for vector in vectors):
            return []
        return vectors

    def _looks_like_noise_group(self, comments: list[dict], domain: str) -> bool:
        return all(self._looks_like_noise(comment, domain) for comment in comments)

    def _looks_like_noise(self, comment: dict, domain: str) -> bool:
        text = comment.get("cleaned_content", "")
        tokens = tokenize(text, domain)
        taxonomy = get_taxonomy(domain)
        domain_terms = {term.lower() for term in taxonomy.domain_terms | GENERAL_DOMAIN_TERMS}
        has_domain_term = any(token.lower() in domain_terms for token in tokens)
        has_signal = (
            self._classification_signal(comment.get("painpoint"))
            or self._classification_signal(comment.get("positive_attribution"))
            or has_domain_term
        )
        stance, _, _ = classify_stance(text, domain)
        if not has_signal and stance == "无关":
            return True
        return len(text.strip()) <= 8 and not has_signal

    def _classification_signal(self, result: dict | None) -> bool:
        if not result:
            return False
        return float(result.get("confidence") or 0) >= 0.6
