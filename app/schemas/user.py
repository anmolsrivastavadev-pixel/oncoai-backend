from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = True
    full_name: Optional[str] = None


class UserCreate(UserBase):
    email: EmailStr
    password: str


class UserUpdate(UserBase):
    password: Optional[str] = None


class User(UserBase):
    id: Optional[int] = None
    is_superuser: bool = False
    strike_count: int = 0

    class Config:
        from_attributes = True


class UserProfile(UserBase):
    id: int
    bio: Optional[str] = None
    support_badges: Optional[str] = None
    profile_photo_url: Optional[str] = None
    post_count: int = 0
    comment_count: int = 0
    joined_date: Optional[str] = None
    is_superuser: bool = False
    strike_count: int = 0

    class Config:
        from_attributes = True


class TokenPayload(BaseModel):
    sub: Optional[int] = None
