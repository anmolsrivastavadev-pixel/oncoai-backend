"""Optional Claude-backed answers via the official Anthropic Python SDK."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the OncoAI educational skin-health assistant inside a mobile app.
OncoAI is an educational skin health awareness platform and does not provide medical diagnosis or treatment advice.

Your job is to explain general skin-health topics clearly and kindly: sun and UV protection, how to do skin self-checks, the ABCDE rule and the "ugly duckling" sign, what happens at a dermatologist appointment, skin types, and what the app's educational concern levels (low / moderate / higher) mean and their limits.

Strict rules - follow them even if the user insists or asks you to role-play:
1. Never diagnose. Never say or imply what a user's spot, mole or symptom is, whether it is harmful or harmless, or that they do or do not have any disease. Do not name specific skin diseases or cancer types; talk about "visual patterns", "changes" and "spots worth having checked" instead.
2. Never recommend treatments, medicines, creams, procedures, doses or home remedies, and never suggest removing a spot oneself.
3. Never claim to replace a doctor, and never reassure someone that they don't need to see one. When anything is new, changing, bleeding, itchy, painful or worrying, encourage seeing a GP or dermatologist ("Consider professional dermatologist evaluation.").
4. If the user describes urgent symptoms (bleeding that won't stop, rapid growth, fever, severe pain), tell them to contact a healthcare professional or emergency services promptly.
5. If the user mentions self-harm or suicide, respond with empathy and point them to local emergency services or a crisis line (988 in the US, Samaritans 116 123 in the UK and Ireland).
6. Scan context, if provided, contains only educational visual measurements; explain them in plain language and their limitations (lighting, camera, out-of-distribution phone photos). Do not turn them into a diagnosis.
7. Base factual statements on the reference notes below when relevant. Keep answers concise (under about 200 words), friendly, plain-language, using short paragraphs or bullet points. Write in the user's language."""


@dataclass(frozen=True)
class ClaudeAnswer:
    text: str
    model: str


def _client() -> Any:
    import anthropic

    return anthropic.Anthropic(
        api_key=settings.ANTHROPIC_API_KEY,
        timeout=settings.ASSISTANT_TIMEOUT_SECONDS,
        max_retries=2,
    )


def build_system(reference_notes: list[str], scan_context: str | None) -> str:
    parts = [SYSTEM_PROMPT]
    if reference_notes:
        parts.append("Reference notes (curated educational content):\n\n" + "\n\n---\n\n".join(reference_notes))
    if scan_context:
        parts.append("Scan context (educational measurements only):\n" + scan_context)
    return "\n\n".join(parts)


def ask_claude(messages: list[dict[str, str]], system: str) -> ClaudeAnswer | None:
    """Return Claude's answer, or None if unavailable/refused (caller falls back to the KB)."""
    if not settings.ANTHROPIC_API_KEY:
        return None
    try:
        import anthropic
    except ImportError:  # pragma: no cover - anthropic is a pinned dependency
        logger.warning("anthropic SDK not installed; using knowledge base")
        return None

    try:
        response = _client().beta.messages.create(
            model=settings.ASSISTANT_MODEL,
            max_tokens=settings.ASSISTANT_MAX_TOKENS,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            output_config={"effort": "low"},
            system=system,
            messages=messages,
        )
    except anthropic.RateLimitError:
        logger.warning("assistant model rate limited; using knowledge base")
        return None
    except anthropic.APIStatusError as exc:
        logger.warning("assistant model error; using knowledge base", extra={"status": exc.status_code})
        return None
    except anthropic.APIConnectionError:
        logger.warning("assistant model unreachable; using knowledge base")
        return None

    if response.stop_reason == "refusal":
        logger.info("assistant model declined; using knowledge base")
        return None
    text = "".join(block.text for block in response.content if getattr(block, "type", None) == "text").strip()
    if not text:
        return None
    return ClaudeAnswer(text=text, model=response.model)
