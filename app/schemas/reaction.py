from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ReactionBase(BaseModel):
    reaction_type: str


class ReactionCreate(ReactionBase):
    pass


class Reaction(ReactionBase):
    id: int
    post_id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ReactionCounts(BaseModel):
    support: int = 0
    strength: int = 0
    hope: int = 0
    helpful: int = 0
    encouragement: int = 0
