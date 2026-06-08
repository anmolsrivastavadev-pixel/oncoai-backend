from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class Notification(BaseModel):
    id: int
    type: str
    message: str
    is_read: bool
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class UnreadCount(BaseModel):
    count: int
