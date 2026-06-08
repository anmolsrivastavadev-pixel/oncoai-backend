from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class CheckInCreate(BaseModel):
    mood: str
    message: Optional[str] = None


class CheckIn(BaseModel):
    id: int
    user_id: int
    mood: str
    message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class Milestone(BaseModel):
    key: str
    label: str
    description: str
    achieved: bool
    progress: float = 0.0
