from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class GroupBase(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    icon: str = "Users"
    is_private: bool = False


class GroupCreate(GroupBase):
    pass


class Group(GroupBase):
    id: int
    created_at: datetime
    created_by: Optional[int] = None
    member_count: int = 0
    is_member: bool = False

    class Config:
        from_attributes = True


class GroupMemberInfo(BaseModel):
    id: int
    user_id: int
    full_name: str
    role: str
    joined_at: datetime
