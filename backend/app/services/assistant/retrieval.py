"""Small TF-IDF retriever over the curated knowledge base (no external dependencies)."""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass

from app.services.assistant.knowledge_base import ARTICLES, Article

_TOKEN = re.compile(r"[a-z0-9]+")
STOPWORDS = frozenset(
    ["a", "an", "and", "are", "as", "at", "be", "but", "by", "can", "do", "does", "for", "from", "how", "i", "if", "in", "is", "it", "its", "me", "my", "of", "on", "or", "should", "so", "that", "the", "this", "to", "was", "what", "when", "where", "which", "who", "why", "will", "with", "you", "your", "am", "have", "has", "had", "there", "their", "they", "them", "we", "our", "us", "any", "some", "about", "into", "than", "then", "too", "very", "just"]
)
KEYWORD_WEIGHT = 3  # keywords count as if they appeared this many times


def tokenize(text: str) -> list[str]:
    tokens = []
    for token in _TOKEN.findall(text.lower()):
        if token in STOPWORDS:
            continue
        if len(token) > 4 and token.endswith("s") and not token.endswith("ss"):
            token = token[:-1]  # crude plural folding: "moles" -> "mole"
        tokens.append(token)
    return tokens


@dataclass(frozen=True)
class Hit:
    article: Article
    score: float


class Retriever:
    def __init__(self, articles: list[Article]) -> None:
        self._articles = articles
        docs: list[Counter[str]] = []
        for article in articles:
            counts = Counter(tokenize(" ".join([article.title, article.summary, *article.body])))
            for keyword in article.keywords:
                for token in tokenize(keyword):
                    counts[token] += KEYWORD_WEIGHT
            docs.append(counts)
        n_docs = len(docs)
        df: Counter[str] = Counter()
        for counts in docs:
            df.update(counts.keys())
        self._idf = {term: math.log((1 + n_docs) / (1 + freq)) + 1.0 for term, freq in df.items()}
        self._vectors = [self._weigh(counts) for counts in docs]

    def _weigh(self, counts: Counter[str]) -> dict[str, float]:
        vector = {t: (1 + math.log(c)) * self._idf.get(t, 0.0) for t, c in counts.items() if t in self._idf}
        norm = math.sqrt(sum(v * v for v in vector.values())) or 1.0
        return {t: v / norm for t, v in vector.items()}

    def search(self, query: str, k: int = 3, min_score: float = 0.05) -> list[Hit]:
        vector = self._weigh(Counter(tokenize(query)))
        hits = []
        for article, doc in zip(self._articles, self._vectors, strict=True):
            score = sum(weight * doc.get(term, 0.0) for term, weight in vector.items())
            if score >= min_score:
                hits.append(Hit(article, round(score, 4)))
        hits.sort(key=lambda hit: hit.score, reverse=True)
        return hits[:k]


retriever = Retriever(ARTICLES)
