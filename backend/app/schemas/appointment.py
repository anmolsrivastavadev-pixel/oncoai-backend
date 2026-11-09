from __future__ import annotations

from datetime import date as Date
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel, UTCDateTime
from app.schemas.dermatologist import DermatologistOut

TIME_PATTERN = r"^([01]\d|2[0-3]):[0-5]\d$"


class AppointmentCreate(BaseModel):
    dermatologist_id: int
    date: Date
    time: str = Field(pattern=TIME_PATTERN)
    reason: str = Field(min_length=1, max_length=1000)
    scan_id: int | None = None


class AppointmentUpdate(BaseModel):
    date: Date | None = None
    time: str | None = Field(default=None, pattern=TIME_PATTERN)
    reason: str | None = Field(default=None, min_length=1, max_length=1000)


class AppointmentOut(ORMModel):
    id: int
    dermatologist: DermatologistOut
    scheduled_at: UTCDateTime
    reason: str
    status: Literal["booked", "cancelled", "completed"]
    scan_id: int | None
    created_at: UTCDateTime
