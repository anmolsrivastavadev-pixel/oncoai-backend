"""Appointment slot logic. Slots are expressed in the dermatologist's local time zone
(30-minute slots, 09:00-17:00, Monday-Friday) and stored as UTC timestamps."""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Appointment, Dermatologist
from app.models.enums import AppointmentStatus

SLOT_MINUTES = 30
DAY_START = time(9, 0)
DAY_END = time(17, 0)


def all_slots() -> list[str]:
    slots: list[str] = []
    current = datetime.combine(date(2000, 1, 3), DAY_START)
    end = datetime.combine(date(2000, 1, 3), DAY_END)
    while current < end:
        slots.append(current.strftime("%H:%M"))
        current += timedelta(minutes=SLOT_MINUTES)
    return slots


SLOTS = all_slots()


def tz_for(derm: Dermatologist) -> ZoneInfo:
    return ZoneInfo(derm.timezone or "UTC")


def to_utc(derm: Dermatologist, day: date, hhmm: str) -> datetime:
    hour, minute = (int(part) for part in hhmm.split(":"))
    local = datetime.combine(day, time(hour, minute), tzinfo=tz_for(derm))
    return local.astimezone(UTC)


def to_local(derm: Dermatologist, moment: datetime) -> datetime:
    return moment.astimezone(tz_for(derm))


def available_slots(
    db: Session, derm: Dermatologist, day: date, *, exclude_appointment_id: int | None = None
) -> list[str]:
    tz = tz_for(derm)
    now_local = datetime.now(UTC).astimezone(tz)
    if day.weekday() >= 5 or day < now_local.date():
        return []
    window_start = datetime.combine(day, time(0, 0), tzinfo=tz).astimezone(UTC)
    window_end = window_start + timedelta(days=1, hours=1)
    query = select(Appointment.scheduled_at).where(
        Appointment.dermatologist_id == derm.id,
        Appointment.status == AppointmentStatus.booked.value,
        Appointment.scheduled_at >= window_start,
        Appointment.scheduled_at < window_end,
    )
    if exclude_appointment_id is not None:
        query = query.where(Appointment.id != exclude_appointment_id)
    booked = {to_local(derm, ts).strftime("%H:%M") for ts in db.scalars(query).all()}
    result = []
    for slot in SLOTS:
        if slot in booked:
            continue
        if to_utc(derm, day, slot) <= datetime.now(UTC):
            continue
        result.append(slot)
    return result


def is_bookable_slot(derm: Dermatologist, day: date, hhmm: str) -> bool:
    """Whether the slot exists in the schedule at all (ignores existing bookings)."""
    if day.weekday() >= 5 or hhmm not in SLOTS:
        return False
    return to_utc(derm, day, hhmm) > datetime.now(UTC)
