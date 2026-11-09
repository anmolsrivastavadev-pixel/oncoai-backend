from __future__ import annotations

from pydantic import BaseModel

from app.schemas.appointment import AppointmentOut
from app.schemas.common import UTCDateTime
from app.schemas.reminder import ReminderOut
from app.schemas.scan import ScanOut, ScanSummary, Symptoms


class Deltas(BaseModel):
    asymmetry: float
    border_irregularity: float
    color_variation: float
    diameter_relative: float
    concern_score: float


class CompareOut(BaseModel):
    a: ScanOut
    b: ScanOut
    deltas: Deltas
    summary: str


class Totals(BaseModel):
    lesions: int
    scans: int
    upcoming_appointments: int


class ConcernBreakdown(BaseModel):
    low: int = 0
    moderate: int = 0
    higher: int = 0


class DayCount(BaseModel):
    date: str
    count: int


class ScorePoint(BaseModel):
    date: str
    lesion_id: int
    lesion_label: str
    concern_score: float


class DashboardOut(BaseModel):
    totals: Totals
    concern_breakdown: ConcernBreakdown
    scans_over_time: list[DayCount]
    score_trend: list[ScorePoint]
    recent_scans: list[ScanSummary]
    next_appointment: AppointmentOut | None
    reminders: list[ReminderOut]


class SymptomLogIn(Symptoms):
    lesion_id: int | None = None


class SymptomLogOut(Symptoms):
    id: int
    lesion_id: int | None
    created_at: UTCDateTime
