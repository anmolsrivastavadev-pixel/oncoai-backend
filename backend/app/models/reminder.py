from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin
from app.models.enums import ReminderKind, check_in


class Reminder(TimestampMixin, Base):
    __tablename__ = "reminders"
    __table_args__ = (
        CheckConstraint(check_in("kind", ReminderKind), name="kind"),
        CheckConstraint("repeat_days IS NULL OR repeat_days > 0", name="repeat_days"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(160))
    kind: Mapped[str] = mapped_column(String(16))
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    done: Mapped[bool] = mapped_column(Boolean, default=False)
    lesion_id: Mapped[int | None] = mapped_column(ForeignKey("lesions.id", ondelete="CASCADE"))
    appointment_id: Mapped[int | None] = mapped_column(
        ForeignKey("appointments.id", ondelete="CASCADE")
    )
    repeat_days: Mapped[int | None] = mapped_column(Integer)
