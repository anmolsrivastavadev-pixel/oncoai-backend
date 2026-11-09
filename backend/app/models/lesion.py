from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import BodyLocation, check_in

if TYPE_CHECKING:
    from app.models.scan import Scan
    from app.models.user import User


class Lesion(TimestampMixin, Base):
    __tablename__ = "lesions"
    __table_args__ = (CheckConstraint(check_in("body_location", BodyLocation), name="body_location"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    label: Mapped[str] = mapped_column(String(80))
    body_location: Mapped[str] = mapped_column(String(32))
    notes: Mapped[str | None] = mapped_column(Text)

    user: Mapped[User] = relationship(back_populates="lesions")
    scans: Mapped[list[Scan]] = relationship(
        back_populates="lesion",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="desc(Scan.created_at)",
    )
