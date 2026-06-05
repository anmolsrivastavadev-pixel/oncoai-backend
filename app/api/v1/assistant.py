"""OncoAI Assistant API - educational chat companion for skin health."""

import json
from typing import Any

from google import genai
from google.genai import types
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app import models
from app.api import deps
from app.core.config import settings

router = APIRouter()

# --- DATA MODELS ---
class ChatMessage(BaseModel):
    """Incoming chat message from the user."""

    message: str

class ChatResponse(BaseModel):
    """Structured response from the AI assistant."""

    response: str
    intent_detected: str
    suggested_action: str | None = None
    disclaimer: str

class ModerationReviewRequest(BaseModel):
    post_id: int
    post_title: str
    post_content: str
    post_category: str
    author_name: str | None = None
    flag_reason: str | None = None

class ModerationReviewResponse(BaseModel):
    safety_rating: str
    toxicity_score: int
    reasoning: str
    recommended_action: str
    category_violated: str | None = None

SYSTEM_PROMPT = """
You are the OncoAI Assistant, a professional educational skin health companion.
Provide accurate information about skin cancer and prevention. NEVER provide a medical diagnosis.
"""

MODERATION_SYSTEM_PROMPT = """
You are the OncoAI Moderation Assistant. Your job is to evaluate community posts for safety.
The platform is a skin health educational community. Flag the following types of content as UNSAFE:
1. Medical misinformation (false cancer cures, anti-treatment rhetoric, guaranteed cures)
2. Harassment, hate speech, or bullying
3. Spam or promotional content
4. Sharing personal health information of others
5. Impersonating medical professionals

For each post, assess: SAFE (no issues), WARNING (borderline/needs attention), or UNSAFE (must be removed).
Provide a toxicity score 0-100. Never allow medical misinformation about cancer to spread.
"""


def _call_gemini(client, model, contents, config):
    response = client.models.generate_content(model=model, contents=contents, config=config)
    if response and response.text:
        return response.text
    raise RuntimeError("AI returned empty response")


def _get_client():
    api_key = settings.GOOGLE_API_KEY
    if not api_key:
        raise HTTPException(status_code=500, detail="Gemini API key not configured")
    return genai.Client(api_key=api_key)


@router.post("/chat", response_model=ChatResponse)
async def companion_chat(
    *,
    db: Session = Depends(deps.get_db),
    chat_in: ChatMessage,
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """Process a chat message and return an AI-generated educational response."""
    user_scans = (
        db.query(models.Scan)
        .filter(models.Scan.user_id == current_user.id)
        .order_by(models.Scan.created_at.desc())
        .all()
    )
    scan_count = len(user_scans)
    api_key = settings.GOOGLE_API_KEY

    if not api_key:
        return {
            "response": "API Key missing.",
            "intent_detected": "ERROR",
            "disclaimer": "Add GOOGLE_API_KEY to .env",
        }

    try:
        client = genai.Client(api_key=api_key)

        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.7,
        )

        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=(
                f"User has {scan_count} scans. "
                f"Question: {chat_in.message}"
            ),
            config=config,
        )

        if response and response.text:
            return {
                "response": response.text,
                "intent_detected": "SUCCESS",
                "disclaimer": "Educational guidance only.",
            }
        raise RuntimeError("AI returned empty response")

    except Exception:
        try:
            client_alt = genai.Client(api_key=api_key)
            resp_alt = client_alt.models.generate_content(
                model="gemini-flash-latest",
                contents=chat_in.message,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT
                ),
            )
            return {
                "response": resp_alt.text,
                "intent_detected": "FALLBACK_SUCCESS",
                "disclaimer": "Educational guidance only.",
            }
        except Exception:
            msg = (
                "I'm having trouble thinking. Please try again later "
                "or check your Gemini API key configuration."
            )
            return {
                "response": msg,
                "intent_detected": "ERROR",
                "disclaimer": "Educational guidance only.",
            }


@router.post("/moderation/review", response_model=ModerationReviewResponse)
async def moderation_review(
    *,
    review_in: ModerationReviewRequest,
    current_user: models.User = Depends(deps.get_current_superuser),
) -> Any:
    """AI-powered safety review of a flagged community post."""
    client = _get_client()

    prompt = (
        f"Review this flagged community post:\n"
        f"Title: {review_in.post_title}\n"
        f"Category: {review_in.post_category}\n"
        f"Author: {review_in.author_name or 'Unknown'}\n"
        f"Flag reason: {review_in.flag_reason or 'Not specified'}\n"
        f"Content: {review_in.post_content}\n\n"
        f"Respond with valid JSON containing: "
        f"safety_rating (SAFE/WARNING/UNSAFE), "
        f"toxicity_score (integer 0-100), "
        f"reasoning (brief explanation), "
        f"recommended_action (DISMISS/HIDE/STRIKE), "
        f"category_violated (misinformation/harassment/spam/fake_cure/other or null)"
    )

    config = types.GenerateContentConfig(
        system_instruction=MODERATION_SYSTEM_PROMPT,
        temperature=0.2,
    )

    try:
        text = _call_gemini(client, "gemini-flash-latest", prompt, config)
        cleaned = text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        result = json.loads(cleaned.strip())
        return ModerationReviewResponse(**result)
    except (json.JSONDecodeError, Exception) as e:
        return ModerationReviewResponse(
            safety_rating="WARNING",
            toxicity_score=50,
            reasoning=f"AI analysis could not complete automatic review. Manual review recommended. Error: {str(e)[:100]}",
            recommended_action="DISMISS",
            category_violated=None,
        )
