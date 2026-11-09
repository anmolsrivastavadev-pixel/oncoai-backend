from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, Query, Response, status
from sqlalchemy import select

from app.api.router import SlashRouter
from app.api.deps import DB, CurrentUser
from app.models import Appointment, Reminder
from app.schemas.common import Items
from app.schemas.reminder import ReminderCreate, ReminderOut, ReminderUpdate
from app.services.scan_service import get_owned_lesion

router = SlashRouter(prefix="/reminders", tags=["reminders"])


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=UTC)


def _owned(db: DB, user_id: int, reminder_id: int) -> Reminder:
    reminder = db.get(Reminder, reminder_id)
    if reminder is None or reminder.user_id != user_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Reminder not found")
    return reminder


@router.get("/", response_model=Items[ReminderOut])
def list_reminders(
    user: CurrentUser,
    db: DB,
    include_done: bool = True,
    limit: int = Query(default=100, ge=1, le=100),
) -> Items[ReminderOut]:
    conditions = [Reminder.user_id == user.id]
    if not include_done:
        conditions.append(Reminder.done.is_(False))
    rows = db.scalars(
        select(Reminder).where(*conditions).order_by(Reminder.done, Reminder.due_at, Reminder.id).limit(limit)
    ).all()
    return Items(items=[ReminderOut.model_validate(r) for r in rows])


@router.post("/", response_model=ReminderOut, status_code=status.HTTP_201_CREATED)
def create_reminder(payload: ReminderCreate, user: CurrentUser, db: DB) -> Reminder:
    if payload.lesion_id is not None:
        get_owned_lesion(db, user.id, payload.lesion_id)
    if payload.appointment_id is not None:
        appt = db.get(Appointment, payload.appointment_id)
        if appt is None or appt.user_id != user.id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Appointment not found")
    reminder = Reminder(
        user_id=user.id,
        title=payload.title.strip(),
        kind=payload.kind.value,
        due_at=_aware(payload.due_at),
        lesion_id=payload.lesion_id,
        appointment_id=payload.appointment_id,
        repeat_days=payload.repeat_days,
    )
    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    return reminder


@router.patch("/{reminder_id}", response_model=ReminderOut)
def update_reminder(reminder_id: int, payload: ReminderUpdate, user: CurrentUser, db: DB) -> Reminder:
    reminder = _owned(db, user.id, reminder_id)
    if payload.title is not None:
        reminder.title = payload.title.strip()
    if payload.due_at is not None:
        reminder.due_at = _aware(payload.due_at)
    if payload.done is not None:
        completing = payload.done and not reminder.done
        reminder.done = payload.done
        if completing and reminder.repeat_days:
            # Recurring reminder: completing it schedules the next occurrence.
            db.add(
                Reminder(
                    user_id=user.id,
                    title=reminder.title,
                    kind=reminder.kind,
                    due_at=reminder.due_at + timedelta(days=reminder.repeat_days),
                    lesion_id=reminder.lesion_id,
                    appointment_id=reminder.appointment_id,
                    repeat_days=reminder.repeat_days,
                )
            )
    db.commit()
    db.refresh(reminder)
    return reminder


@router.delete("/{reminder_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reminder(reminder_id: int, user: CurrentUser, db: DB) -> Response:
    db.delete(_owned(db, user.id, reminder_id))
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
