from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class DeviceTokenRegister(BaseModel):
    token: str
    platform: str = "android"


class MessageCreate(BaseModel):
    content: str


class MessageResponse(BaseModel):
    id: int
    sender_id: int
    receiver_id: int
    content: str
    is_read: bool
    sender_name: Optional[str] = None
    created_at: datetime


class Conversation(BaseModel):
    user_id: int
    user_name: str
    last_message: str
    last_message_time: datetime
    unread_count: int


class DoctorVerifyRequest(BaseModel):
    doctor_id: int
    is_verified: bool


class AnalyticsResponse(BaseModel):
    total_users: int
    total_scans: int
    total_posts: int
    total_comments: int
    total_reactions: int
    total_groups: int
    flagged_posts: int
    banned_users: int
    scans_today: int
    posts_today: int
    new_users_today: int
    scan_classifications: dict = {}
    mood_distribution: dict = {}
    daily_scans: List[dict] = []
    daily_posts: List[dict] = []


class EmailTest(BaseModel):
    email: str
    subject: str
    body: str
