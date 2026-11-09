from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class SymptomLog(TimestampMixin, Base):
    __tablename__ = "symptom_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    lesion_id: Mapped[int | None] = mapped_column(
        ForeignKey("lesions.id", ondelete="CASCADE"), index=True
    )
    itching: Mapped[bool] = mapped_column(Boolean, default=False)
    bleeding: Mapped[bool] = mapped_column(Boolean, default=False)
    pain: Mapped[bool] = mapped_column(Boolean, default=False)
    changed_size: Mapped[bool] = mapped_column(Boolean, default=False)
    changed_color: Mapped[bool] = mapped_column(Boolean, default=False)
    changed_shape: Mapped[bool] = mapped_column(Boolean, default=False)
    new_spot: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str | None] = mapped_column(Text)
