from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.models.enums import PostTopic, ReactionKind
from app.schemas.common import UTCDateTime


class Author(BaseModel):
    id: int | None
    display_name: str


class PostCreate(BaseModel):
    title: str = Field(min_length=3, max_length=150)
    body: str = Field(min_length=1, max_length=5000)
    topic: PostTopic
    anonymous: bool = False


class CommentCreate(BaseModel):
    body: str = Field(min_length=1, max_length=2000)
    anonymous: bool = False


class ReactionIn(BaseModel):
    kind: ReactionKind


class ReportIn(BaseModel):
    reason: str = Field(min_length=1, max_length=500)


class ReactionCounts(BaseModel):
    support: int = 0
    hug: int = 0
    strength: int = 0
    relate: int = 0


class CommentOut(BaseModel):
    id: int
    post_id: int
    body: str
    author: Author
    created_at: UTCDateTime
    is_mine: bool


class PostOut(BaseModel):
    id: int
    title: str
    body: str
    topic: PostTopic
    author: Author
    created_at: UTCDateTime
    comment_count: int
    reactions: ReactionCounts
    my_reactions: list[ReactionKind]
    is_mine: bool
    status: Literal["visible", "removed"]
    under_review: bool = False


class PostDetail(PostOut):
    comments: list[CommentOut]


class ReactionsOut(BaseModel):
    reactions: ReactionCounts
    my_reactions: list[ReactionKind]


class ReportCreated(BaseModel):
    id: int
    status: Literal["open"] = "open"


class ReportOut(BaseModel):
    id: int
    target_type: Literal["post", "comment"]
    post_id: int
    comment_id: int | None
    reason: str
    status: Literal["open", "dismissed", "actioned"]
    created_at: UTCDateTime
    content_preview: str
    open_report_count: int
    reporter_id: int


class ResolveIn(BaseModel):
    action: Literal["dismiss", "remove_content"]
