from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from typing import Annotated, Literal

from fastapi import HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.router import SlashRouter
from app.api.deps import DB, CurrentUser, Paging
from app.api.v1.dermatologists import get_dermatologist
from app.models import Appointment, Dermatologist, Reminder
from app.models.enums import AppointmentStatus, ReminderKind
from app.schemas.appointment import AppointmentCreate, AppointmentOut, AppointmentUpdate
from app.schemas.common import Page
from app.services import scan_service
from app.services.booking import available_slots, is_bookable_slot, to_local, to_utc

router = SlashRouter(prefix="/appointments", tags=["appointments"])

SLOT_TAKEN = "That time slot is no longer available. Please choose another time."
REMINDER_LEAD = timedelta(hours=24)


def _owned(db: Session, user_id: int, appointment_id: int) -> Appointment:
    appt = db.get(Appointment, appointment_id)
    if appt is None or appt.user_id != user_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Appointment not found")
    return appt


def _reminder_due(scheduled_at: datetime) -> datetime:
    return max(scheduled_at - REMINDER_LEAD, datetime.now(UTC))


def _validate_slot(
    db: Session, derm: Dermatologist, day: date, hhmm: str, exclude_id: int | None = None
) -> datetime:
    if not is_bookable_slot(derm, day, hhmm):
        raise HTTPException(
            422,
            "Choose a future 30-minute slot between 09:00 and 17:00, Monday to Friday "
            "(the dermatologist's local time).",
        )
    if hhmm not in available_slots(db, derm, day, exclude_appointment_id=exclude_id):
        raise HTTPException(status.HTTP_409_CONFLICT, SLOT_TAKEN)
    return to_utc(derm, day, hhmm)


def _commit_or_conflict(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, SLOT_TAKEN) from exc


def _reminder_title(derm: Dermatologist) -> str:
    return f"Appointment with {derm.name} tomorrow"[:160]


@router.get("/", response_model=Page[AppointmentOut])
def list_appointments(
    user: CurrentUser,
    db: DB,
    paging: Paging,
    status_filter: Annotated[Literal["upcoming", "past", "all"], Query(alias="status")] = "all",
) -> Page[AppointmentOut]:
    now = datetime.now(UTC)
    conditions = [Appointment.user_id == user.id]
    order = Appointment.scheduled_at.desc()
    if status_filter == "upcoming":
        conditions += [
            Appointment.status == AppointmentStatus.booked.value,
            Appointment.scheduled_at >= now,
        ]
        order = Appointment.scheduled_at.asc()
    elif status_filter == "past":
        conditions.append(
            or_(Appointment.scheduled_at < now, Appointment.status != AppointmentStatus.booked.value)
        )
    total = db.scalar(select(func.count(Appointment.id)).where(*conditions)) or 0
    rows = db.scalars(
        select(Appointment).where(*conditions).order_by(order, Appointment.id).limit(paging.limit).offset(paging.offset)
    ).all()
    return Page(items=[AppointmentOut.model_validate(r) for r in rows], total=total)


@router.post("/", response_model=AppointmentOut, status_code=status.HTTP_201_CREATED)
def book_appointment(payload: AppointmentCreate, user: CurrentUser, db: DB) -> Appointment:
    derm = get_dermatologist(db, payload.dermatologist_id)
    if not derm.accepts_new_patients:
        raise HTTPException(422, "This dermatologist is not currently accepting new patients.")
    if payload.scan_id is not None:
        scan_service.get_owned_scan(db, user.id, payload.scan_id)
    scheduled_at = _validate_slot(db, derm, payload.date, payload.time)
    appt = Appointment(
        user_id=user.id,
        dermatologist_id=derm.id,
        scan_id=payload.scan_id,
        scheduled_at=scheduled_at,
        reason=payload.reason.strip(),
        status=AppointmentStatus.booked.value,
    )
    db.add(appt)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, SLOT_TAKEN) from exc
    db.add(
        Reminder(
            user_id=user.id,
            title=_reminder_title(derm),
            kind=ReminderKind.appointment.value,
            due_at=_reminder_due(scheduled_at),
            appointment_id=appt.id,
        )
    )
    _commit_or_conflict(db)
    db.refresh(appt)
    return appt


@router.patch("/{appointment_id}", response_model=AppointmentOut)
def reschedule_appointment(
    appointment_id: int, payload: AppointmentUpdate, user: CurrentUser, db: DB
) -> Appointment:
    appt = _owned(db, user.id, appointment_id)
    if appt.status != AppointmentStatus.booked.value:
        raise HTTPException(status.HTTP_409_CONFLICT, "Only booked appointments can be changed.")
    derm = appt.dermatologist
    if payload.date is not None or payload.time is not None:
        local = to_local(derm, appt.scheduled_at)
        day = payload.date or local.date()
        hhmm = payload.time or local.strftime("%H:%M")
        new_time = _validate_slot(db, derm, day, hhmm, exclude_id=appt.id)
        if new_time != appt.scheduled_at:
            appt.scheduled_at = new_time
            for reminder in db.scalars(
                select(Reminder).where(
                    Reminder.appointment_id == appt.id,
                    Reminder.kind == ReminderKind.appointment.value,
                    Reminder.done.is_(False),
                )
            ):
                reminder.due_at = _reminder_due(new_time)
    if payload.reason is not None:
        appt.reason = payload.reason.strip()
    _commit_or_conflict(db)
    db.refresh(appt)
    return appt


@router.post("/{appointment_id}/cancel", response_model=AppointmentOut)
def cancel_appointment(appointment_id: int, user: CurrentUser, db: DB) -> Appointment:
    appt = _owned(db, user.id, appointment_id)
    if appt.status == AppointmentStatus.completed.value:
        raise HTTPException(status.HTTP_409_CONFLICT, "Completed appointments cannot be cancelled.")
    if appt.status == AppointmentStatus.booked.value:
        appt.status = AppointmentStatus.cancelled.value
        for reminder in db.scalars(
            select(Reminder).where(Reminder.appointment_id == appt.id, Reminder.done.is_(False))
        ):
            db.delete(reminder)
        db.commit()
        db.refresh(appt)
    return appt
