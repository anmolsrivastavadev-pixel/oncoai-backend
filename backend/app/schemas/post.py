from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional, Dict


class CommentBase(BaseModel):
    content: str


class CommentCreate(CommentBase):
    post_id: int


class CommentContent(BaseModel):
    content: str


class Comment(CommentBase):
    id: int
    created_at: datetime
    user_id: int
    author_name: Optional[str] = None
    is_flagged: bool = False

    class Config:
        from_attributes = True


class PostBase(BaseModel):
    title: str
    content: str
    category: str


class PostCreate(PostBase):
    image_url: Optional[str] = None
    group_id: Optional[int] = None
    is_anonymous: bool = False


class PostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None


class Post(PostBase):
    id: int
    created_at: datetime
    user_id: Optional[int] = None
    author_name: Optional[str] = None
    image_url: Optional[str] = None
    is_flagged: bool = False
    pinned: bool = False
    group_id: Optional[int] = None
    is_anonymous: bool = False
    comment_count: int = 0
    reaction_counts: Dict[str, int] = {}
    user_reaction: Optional[str] = None
    comments: List[Comment] = []

    class Config:
        from_attributes = True


class FlagCreate(BaseModel):
    reason: str
