from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class StrikeCreate(BaseModel):
    reason: str


class ModerationAction(BaseModel):
    action: str
    detail: Optional[str] = None


class QueuedPost(BaseModel):
    id: int
    title: str
    content: str
    category: str
    author_name: Optional[str] = None
    author_email: Optional[str] = None
    author_id: int
    is_flagged: bool
    flag_reason: Optional[str] = None
    flagged_by: Optional[int] = None
    is_hidden: bool
    pinned: bool
    created_at: datetime
    comment_count: int = 0


class ModerationStats(BaseModel):
    flagged_posts: int = 0
    hidden_posts: int = 0
    resolved_today: int = 0
    total_strikes_issued: int = 0
    banned_users: int = 0
    active_users: int = 0


class UserSummary(BaseModel):
    id: int
    full_name: str
    email: str
    is_active: bool
    is_superuser: bool
    strike_count: int
    last_strike_at: Optional[datetime] = None
    post_count: int = 0
