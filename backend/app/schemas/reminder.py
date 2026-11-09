from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import ReminderKind
from app.schemas.common import ORMModel, UTCDateTime


class ReminderCreate(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    kind: ReminderKind
    due_at: datetime
    lesion_id: int | None = None
    appointment_id: int | None = None
    repeat_days: int | None = Field(default=None, ge=1, le=365)


class ReminderUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=160)
    due_at: datetime | None = None
    done: bool | None = None


class ReminderOut(ORMModel):
    id: int
    title: str
    kind: ReminderKind
    due_at: UTCDateTime
    done: bool
    lesion_id: int | None
    appointment_id: int | None
    repeat_days: int | None
