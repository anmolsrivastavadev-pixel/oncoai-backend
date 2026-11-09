"""Assistant orchestration: input guardrails -> retrieval -> Claude (optional) -> output filter."""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.models import Scan
from app.schemas.assistant import ChatIn, ChatOut, Safety, Source as SourceOut, TopicOut
from app.services.assistant import claude_provider, guardrails
from app.services.assistant.knowledge_base import ARTICLES, ARTICLES_BY_ID, Article, Source
from app.services.assistant.retrieval import retriever

logger = logging.getLogger(__name__)

MAX_HISTORY = 12
DEFAULT_SUGGESTIONS = [
    "What is the ABCDE rule?",
    "How do I do a monthly skin self-exam?",
    "How do I protect my skin from the sun?",
]
NO_MATCH_REPLY = (
    "I'm OncoAI's educational assistant. I can explain things like the ABCDE rule for "
    "checking moles, how to do a skin self-exam, sun protection and the UV index, skin types, "
    "what happens at a dermatologist appointment, and what your OncoAI scan result means. "
    "What would you like to know?"
)


def list_topics() -> list[TopicOut]:
    return [TopicOut(id=a.id, title=a.title, summary=a.summary) for a in ARTICLES if a.listed]


def _sources(sources: list[Source]) -> list[SourceOut]:
    unique = {s.url: s for s in sources}
    return [SourceOut(title=s.title, url=s.url) for s in unique.values()]


def _suggestions(articles: list[Article]) -> list[str]:
    items: list[str] = []
    for article in articles:
        items.extend(article.questions)
    items.extend(DEFAULT_SUGGESTIONS)
    return list(dict.fromkeys(items))[:3]


def kb_reply(articles: list[Article]) -> str:
    if not articles:
        return NO_MATCH_REPLY
    top = articles[0]
    return f"{top.title}\n\n" + "\n\n".join(top.body)


def scan_context_text(scan: Scan) -> str:
    f = scan.features
    return (
        f"Concern level: {scan.concern_level} (score {scan.concern_score:.0f}/100). "
        f"Photo quality ok: {scan.quality.get('ok')}. "
        f"Asymmetry {f.get('asymmetry')}, border irregularity {f.get('border_irregularity')}, "
        f"colour variation {f.get('color_variation')}, distinct colour tones {f.get('color_count')}, "
        f"relative size {f.get('diameter_relative')}% of frame. Analysis type: {scan.model_kind}."
    )


def _conversation(payload: ChatIn) -> list[dict[str, str]]:
    messages = [{"role": m.role, "content": m.content} for m in payload.messages][-MAX_HISTORY:]
    while messages and messages[0]["role"] != "user":
        messages.pop(0)
    return messages


def chat(db: Session, payload: ChatIn, scan: Scan | None) -> ChatOut:
    last_user = next((m.content for m in reversed(payload.messages) if m.role == "user"), "")

    guard = guardrails.check_input(last_user)
    if guard is not None:
        logger.info("assistant input guardrail", extra={"reason": guard.reason})
        return ChatOut(
            reply=guard.reply,
            sources=_sources(guard.sources),
            suggestions=guard.suggestions,
            provider="knowledge_base",
            safety=Safety(redirected=True, reason=guard.reason),
        )

    query = last_user
    if scan is not None and len(last_user.split()) < 12:
        query += " oncoai scan result concern level"
    hits = retriever.search(query, k=3)
    articles = [hit.article for hit in hits]
    if scan is not None and ARTICLES_BY_ID["understanding-results"] not in articles:
        articles.append(ARTICLES_BY_ID["understanding-results"])
    sources = _sources([s for a in articles for s in a.sources])
    suggestions = _suggestions(articles)

    messages = _conversation(payload)
    if messages:
        notes = [f"# {a.title}\n" + "\n".join(a.body) for a in articles]
        system = claude_provider.build_system(notes, scan_context_text(scan) if scan else None)
        answer = claude_provider.ask_claude(messages, system)
        if answer is not None:
            if guardrails.output_violates(answer.text):
                logger.warning("assistant output guardrail triggered")
                return ChatOut(
                    reply=guardrails.OUTPUT_REDIRECT + "\n\n" + kb_reply(articles),
                    sources=sources,
                    suggestions=suggestions,
                    provider="knowledge_base",
                    safety=Safety(redirected=True, reason=guardrails.OUTPUT_FILTERED),
                )
            return ChatOut(
                reply=answer.text,
                sources=sources,
                suggestions=suggestions,
                provider="claude",
                safety=Safety(redirected=False),
            )

    return ChatOut(
        reply=kb_reply(articles),
        sources=sources if articles else [],
        suggestions=suggestions,
        provider="knowledge_base",
        safety=Safety(redirected=False),
    )
