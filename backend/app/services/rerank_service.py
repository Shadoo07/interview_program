from __future__ import annotations

import math
import re
from collections.abc import Iterable
from dataclasses import dataclass

from app.schemas.knowledge_schema import KnowledgeSearchResult


@dataclass
class RerankOptions:
    role_family: str = ""
    version: str = ""


def rerank_results(
    query: str,
    results: Iterable[KnowledgeSearchResult],
    options: RerankOptions | None = None,
) -> list[KnowledgeSearchResult]:
    options = options or RerankOptions()
    query_tokens = tokenize(query)
    reranked: list[KnowledgeSearchResult] = []

    for result in results:
        lexical = lexical_score(query_tokens, result.content)
        phrase = phrase_score(query, result.content)
        metadata = metadata_boost(result, options)
        retrieval = normalize_retrieval_score(result.score)
        length = length_penalty(result.content)

        rerank_score = 0.48 * retrieval + 0.32 * lexical + 0.12 * phrase + 0.08 * metadata
        rerank_score = max(0.0, min(1.0, rerank_score * length))
        result.retrieval_score = round(float(result.score), 4)
        result.rerank_score = round(rerank_score, 4)
        result.score = result.rerank_score
        reranked.append(result)

    reranked.sort(key=lambda item: (item.rerank_score, item.retrieval_score), reverse=True)
    return reranked


def tokenize(text: str) -> list[str]:
    tokens = re.findall(r"[A-Za-z0-9_+#.-]+|[\u4e00-\u9fff]{2,}", text.lower())
    stop_words = {"and", "or", "the", "with", "for", "岗位", "要求", "能力", "熟悉", "负责"}
    return [token for token in tokens if token not in stop_words]


def lexical_score(query_tokens: list[str], content: str) -> float:
    if not query_tokens:
        return 0.0
    content_lower = content.lower()
    matched = 0
    weighted_hits = 0.0
    for token in query_tokens:
        count = content_lower.count(token)
        if count:
            matched += 1
            weighted_hits += min(1.0 + math.log(count), 2.2)
    coverage = matched / len(query_tokens)
    density = weighted_hits / max(len(query_tokens), 1)
    return min(1.0, 0.7 * coverage + 0.3 * density)


def phrase_score(query: str, content: str) -> float:
    query_terms = [term for term in re.split(r"[\s,，。；;、]+", query.lower()) if len(term) >= 3]
    if not query_terms:
        return 0.0
    content_lower = content.lower()
    hits = sum(1 for term in query_terms[:30] if term in content_lower)
    return min(1.0, hits / min(len(query_terms), 30))


def metadata_boost(result: KnowledgeSearchResult, options: RerankOptions) -> float:
    score = 0.0
    if options.role_family and result.role_family == options.role_family:
        score += 0.45
    if options.version and result.version == options.version:
        score += 0.25
    if result.status == "published":
        score += 0.15
    if result.section_title and result.section_title != "正文":
        score += 0.15
    return min(score, 1.0)


def normalize_retrieval_score(score: float) -> float:
    if score <= 0:
        return 0.0
    if score > 1:
        return min(score / 100.0, 1.0)
    return min(score, 1.0)


def length_penalty(content: str) -> float:
    length = len(content)
    if 120 <= length <= 1200:
        return 1.0
    if length < 60:
        return 0.82
    return 0.9
