from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any

from app.taxonomies import get_taxonomy


CHINESE_STOPWORDS = {
    "什么",
    "就是",
    "可以",
    "没有",
    "感觉",
    "可能",
    "一个",
    "这个",
    "那个",
    "真的",
    "不是",
    "但是",
    "还是",
    "怎么",
    "这么",
    "那么",
    "已经",
    "因为",
    "所以",
    "如果",
    "觉得",
    "有点",
    "一下",
    "一样",
    "现在",
    "直接",
    "评论",
    "用户",
    "帖子",
    "大家",
    "我们",
    "他们",
    "你们",
    "the",
    "and",
    "for",
    "with",
    "from",
    "this",
    "that",
    "too",
    "will",
    "story",
    "really",
    "trust",
    "again",
    "summer",
    "master",
    "interesting",
    "amazing",
    "hhh",
}

GENERAL_DOMAIN_TERMS = {
    "NBA",
    "选秀",
    "乐透",
    "首轮",
    "次轮",
    "状元",
    "榜眼",
    "探花",
    "顺位",
    "模板",
    "球探",
    "球队",
    "新秀",
    "培养",
    "投篮",
    "防守",
    "对抗",
    "伤病",
    "天赋",
    "潜力",
    "适配",
    "小红书",
    "弗拉格",
    "迪班萨",
    "皮特森",
    "布泽尔",
    "AJ",
    "dp",
    "Flagg",
    "Dybantsa",
    "Peterson",
    "Boozer",
    "NCAA",
}


def tokenize(text: str, domain: str = "game") -> list[str]:
    """Tokenize Chinese comments with domain phrase matching and stopword filtering."""

    cleaned = _normalize(text)
    if not cleaned:
        return []

    taxonomy = get_taxonomy(domain)
    domain_terms = sorted(taxonomy.domain_terms | GENERAL_DOMAIN_TERMS, key=len, reverse=True)
    domain_term_lowers = {term.lower() for term in domain_terms}
    tokens: list[str] = []
    lowered = cleaned.lower()

    for term in domain_terms:
        term = term.strip()
        if len(term) <= 1 or term.lower() in CHINESE_STOPWORDS:
            continue
        if term.lower() in lowered:
            tokens.append(term)

    for word in re.findall(r"[A-Za-z][A-Za-z0-9_-]{1,}|[\u4e00-\u9fff]{2,}", cleaned):
        if _keep_token(word):
            word_lower = word.lower()
            if re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{1,}", word):
                tokens.append(word)
            elif word_lower in domain_term_lowers:
                tokens.append(word)
            elif len(word) <= 6 and any(term in word_lower for term in domain_term_lowers if len(term) >= 2):
                tokens.append(word)

    deduped: list[str] = []
    seen: set[str] = set()
    for token in tokens:
        normalized = token.strip()
        if not _keep_token(normalized):
            continue
        key = normalized.lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(normalized)
    return deduped


def tfidf_wordcloud(
    comments: list[dict[str, Any]],
    domain: str = "game",
    sentiment: str | None = None,
    limit: int = 60,
) -> list[dict[str, float | str]]:
    """Build weighted word-cloud items using TF-IDF and domain term boosts."""

    docs: list[list[str]] = []
    for comment in comments:
        if comment.get("is_duplicate"):
            continue
        if sentiment and not _sentiment_matches(comment, sentiment):
            continue
        tokens = tokenize(str(comment.get("cleaned_content") or comment.get("content") or ""), domain)
        if tokens:
            docs.append(tokens)
    if not docs:
        return []

    taxonomy = get_taxonomy(domain)
    domain_terms = {term.lower() for term in taxonomy.domain_terms | GENERAL_DOMAIN_TERMS}
    doc_count = len(docs)
    df: Counter[str] = Counter()
    tf: Counter[str] = Counter()
    display: dict[str, str] = {}
    for tokens in docs:
        local = Counter(token.lower() for token in tokens)
        tf.update(local)
        df.update(local.keys())
        for token in tokens:
            display.setdefault(token.lower(), token)

    scores: list[tuple[str, float]] = []
    for token, freq in tf.items():
        idf = math.log((doc_count + 1) / (df[token] + 1)) + 1
        boost = 1.75 if token in domain_terms else 1.0
        if len(token) >= 4 and any(term in token for term in domain_terms):
            boost = max(boost, 1.35)
        scores.append((display[token], freq * idf * boost))

    if not scores:
        return []
    max_score = max(score for _, score in scores) or 1.0
    ranked = sorted(scores, key=lambda item: item[1], reverse=True)[:limit]
    return [{"word": word, "weight": round(1 + score / max_score * 9, 3)} for word, score in ranked]


def _normalize(text: str) -> str:
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"@\S+", " ", text)
    text = re.sub(r"#([^#]+)#", r" \1 ", text)
    text = re.sub(r"[，。！？、；：,.!?;:()\[\]{}<>《》“”\"'|/\\\-]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _keep_token(token: str) -> bool:
    token = token.strip()
    if len(token) <= 1:
        return False
    if token.lower() in CHINESE_STOPWORDS:
        return False
    if token.isdigit():
        return False
    if re.fullmatch(r"[0-9a-zA-Z_-]+", token) and len(token) <= 2:
        return False
    return True


def _meaningful_ngrams(text: str) -> list[str]:
    chunks: list[str] = []
    for size in (4, 3, 2):
        for index in range(0, max(0, len(text) - size + 1)):
            token = text[index : index + size]
            if _keep_token(token) and not any(stop in token for stop in CHINESE_STOPWORDS):
                chunks.append(token)
    return chunks[:8]


def _sentiment_matches(comment: dict[str, Any], sentiment: str) -> bool:
    result = comment.get("sentiment") or {}
    label = str(result.get("label") or "")
    score = float(result.get("score") or 0)
    if sentiment == "positive":
        return score > 0.1 or label.endswith("positive")
    if sentiment == "negative":
        return score < -0.1 or label.endswith("negative")
    return True
