from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import DisclaimerMixin


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class ChatContext(BaseModel):
    scan_id: int | None = None


class ChatIn(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1, max_length=40)
    context: ChatContext | None = None


class Source(BaseModel):
    title: str
    url: str


class Safety(BaseModel):
    redirected: bool
    reason: str | None = None


class ChatOut(DisclaimerMixin):
    reply: str
    sources: list[Source]
    suggestions: list[str]
    provider: Literal["claude", "knowledge_base"]
    safety: Safety


class TopicOut(BaseModel):
    id: str
    title: str
    summary: str
