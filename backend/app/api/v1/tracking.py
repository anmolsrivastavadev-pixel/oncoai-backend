from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from fastapi import Query, status
from sqlalchemy import func, select

from app.api.router import SlashRouter
from app.api.deps import DB, CurrentUser, Paging
from app.models import Appointment, Lesion, Reminder, Scan, SymptomLog
from app.models.enums import AppointmentStatus
from app.schemas.appointment import AppointmentOut
from app.schemas.common import Items
from app.schemas.reminder import ReminderOut
from app.schemas.tracking import (
    CompareOut,
    ConcernBreakdown,
    DashboardOut,
    DayCount,
    Deltas,
    ScorePoint,
    SymptomLogIn,
    SymptomLogOut,
    Totals,
)
from app.services import scan_service

router = SlashRouter(prefix="/tracking", tags=["tracking"])

TREND_DAYS = 90
STABLE_THRESHOLD = 5.0

FEATURE_NAMES = {
    "asymmetry": "shape asymmetry",
    "border_irregularity": "border irregularity",
    "color_variation": "colour variation",
    "diameter_relative": "relative size in the frame",
}


def _describe_change(name: str, delta: float) -> str:
    if abs(delta) < STABLE_THRESHOLD:
        return f"{name} stayed about the same"
    direction = "increased" if delta > 0 else "decreased"
    return f"{name} {direction} by {abs(delta):.0f} points"


def compare_summary(a: Scan, b: Scan, deltas: Deltas) -> str:
    parts = [_describe_change(label, getattr(deltas, key)) for key, label in FEATURE_NAMES.items()]
    first = a.created_at.date().isoformat()
    second = b.created_at.date().isoformat()
    text = (
        f"Comparing the photo from {first} with the photo from {second}: "
        + "; ".join(parts)
        + f". The overall visual concern score went from {a.concern_score:.0f} to {b.concern_score:.0f}"
        f" ({a.concern_level} to {b.concern_level})."
    )
    notable = [k for k in FEATURE_NAMES if getattr(deltas, k) >= STABLE_THRESHOLD * 2]
    if notable or deltas.concern_score >= STABLE_THRESHOLD * 2 or b.concern_level == "higher":
        text += (
            " Some visual measurements changed noticeably. Consider professional dermatologist "
            "evaluation, especially if you have also noticed the spot changing."
        )
    else:
        text += " No large visual change was measured between these photos."
    text += (
        " Measurements from photos vary with lighting, angle and distance, so take follow-up "
        "photos in similar conditions. This comparison is educational and is not a diagnosis."
    )
    return text


@router.get("/compare", response_model=CompareOut)
def compare(
    user: CurrentUser,
    db: DB,
    a: int = Query(description="Earlier scan id"),
    b: int = Query(description="Later scan id"),
) -> CompareOut:
    scan_a = scan_service.get_owned_scan(db, user.id, a)
    scan_b = scan_service.get_owned_scan(db, user.id, b)
    fa, fb = scan_a.features, scan_b.features
    deltas = Deltas(
        **{k: round(float(fb.get(k, 0)) - float(fa.get(k, 0)), 1) for k in FEATURE_NAMES},
        concern_score=round(scan_b.concern_score - scan_a.concern_score, 1),
    )
    return CompareOut(
        a=scan_service.to_out(scan_a),
        b=scan_service.to_out(scan_b),
        deltas=deltas,
        summary=compare_summary(scan_a, scan_b, deltas),
    )


@router.get("/dashboard", response_model=DashboardOut)
def dashboard(user: CurrentUser, db: DB) -> DashboardOut:
    now = datetime.now(UTC)
    lesions = db.scalar(select(func.count(Lesion.id)).where(Lesion.user_id == user.id)) or 0
    scans = db.scalar(select(func.count(Scan.id)).where(Scan.user_id == user.id)) or 0
    upcoming_filter = (
        Appointment.user_id == user.id,
        Appointment.status == AppointmentStatus.booked.value,
        Appointment.scheduled_at >= now,
    )
    upcoming = db.scalar(select(func.count(Appointment.id)).where(*upcoming_filter)) or 0

    latest_levels = db.execute(
        select(Scan.lesion_id, Scan.concern_level)
        .where(Scan.user_id == user.id)
        .distinct(Scan.lesion_id)
        .order_by(Scan.lesion_id, Scan.created_at.desc(), Scan.id.desc())
    ).all()
    breakdown = ConcernBreakdown()
    for _, level in latest_levels:
        setattr(breakdown, level, getattr(breakdown, level) + 1)

    start_day = now.date() - timedelta(days=TREND_DAYS - 1)
    start = datetime.combine(start_day, datetime.min.time(), tzinfo=UTC)
    day_col = func.date(func.timezone("UTC", Scan.created_at))
    counts: dict[date, int] = {
        row[0]: row[1]
        for row in db.execute(
            select(day_col, func.count(Scan.id))
            .where(Scan.user_id == user.id, Scan.created_at >= start)
            .group_by(day_col)
        ).all()
    }
    scans_over_time = [
        DayCount(date=(start_day + timedelta(days=i)).isoformat(), count=counts.get(start_day + timedelta(days=i), 0))
        for i in range(TREND_DAYS)
    ]

    trend_rows = db.execute(
        select(Scan.created_at, Scan.lesion_id, Lesion.label, Scan.concern_score)
        .join(Lesion, Lesion.id == Scan.lesion_id)
        .where(Scan.user_id == user.id, Scan.created_at >= start)
        .order_by(Scan.created_at.asc(), Scan.id.asc())
        .limit(500)
    ).all()
    score_trend = [
        ScorePoint(
            date=created.astimezone(UTC).date().isoformat(),
            lesion_id=lesion_id,
            lesion_label=label,
            concern_score=score,
        )
        for created, lesion_id, label, score in trend_rows
    ]

    recent = db.scalars(
        select(Scan).where(Scan.user_id == user.id).order_by(Scan.created_at.desc(), Scan.id.desc()).limit(5)
    ).all()
    next_appt = db.scalar(select(Appointment).where(*upcoming_filter).order_by(Appointment.scheduled_at).limit(1))
    reminders = db.scalars(
        select(Reminder)
        .where(Reminder.user_id == user.id, Reminder.done.is_(False))
        .order_by(Reminder.due_at.asc())
        .limit(5)
    ).all()
    return DashboardOut(
        totals=Totals(lesions=lesions, scans=scans, upcoming_appointments=upcoming),
        concern_breakdown=breakdown,
        scans_over_time=scans_over_time,
        score_trend=score_trend,
        recent_scans=[scan_service.to_summary(s) for s in recent],
        next_appointment=AppointmentOut.model_validate(next_appt) if next_appt else None,
        reminders=[ReminderOut.model_validate(r) for r in reminders],
    )


@router.get("/symptoms", response_model=Items[SymptomLogOut])
def list_symptoms(
    user: CurrentUser, db: DB, paging: Paging, lesion_id: int | None = None
) -> Items[SymptomLogOut]:
    conditions = [SymptomLog.user_id == user.id]
    if lesion_id is not None:
        conditions.append(SymptomLog.lesion_id == lesion_id)
    logs = db.scalars(
        select(SymptomLog)
        .where(*conditions)
        .order_by(SymptomLog.created_at.desc(), SymptomLog.id.desc())
        .limit(paging.limit)
        .offset(paging.offset)
    ).all()
    return Items(items=[SymptomLogOut.model_validate(log, from_attributes=True) for log in logs])


@router.post("/symptoms", response_model=SymptomLogOut, status_code=status.HTTP_201_CREATED)
def create_symptom_log(payload: SymptomLogIn, user: CurrentUser, db: DB) -> SymptomLogOut:
    if payload.lesion_id is not None:
        scan_service.get_owned_lesion(db, user.id, payload.lesion_id)
    log = SymptomLog(user_id=user.id, **payload.model_dump())
    db.add(log)
    db.commit()
    db.refresh(log)
    return SymptomLogOut.model_validate(log, from_attributes=True)
