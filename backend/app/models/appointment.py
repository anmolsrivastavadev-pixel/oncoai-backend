from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import AppointmentStatus, check_in

if TYPE_CHECKING:
    from app.models.dermatologist import Dermatologist


class Appointment(TimestampMixin, Base):
    __tablename__ = "appointments"
    __table_args__ = (
        CheckConstraint(check_in("status", AppointmentStatus), name="status"),
        # One active booking per dermatologist per slot; cancelled rows don't block.
        Index(
            "uq_appointments_active_slot",
            "dermatologist_id",
            "scheduled_at",
            unique=True,
            postgresql_where=text("status = 'booked'"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    dermatologist_id: Mapped[int] = mapped_column(
        ForeignKey("dermatologists.id", ondelete="CASCADE")
    )
    scan_id: Mapped[int | None] = mapped_column(ForeignKey("scans.id", ondelete="SET NULL"))
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    reason: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(16), default=AppointmentStatus.booked.value)

    dermatologist: Mapped[Dermatologist] = relationship(lazy="joined")
