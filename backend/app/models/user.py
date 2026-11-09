from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Date, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import Role, check_in

if TYPE_CHECKING:
    from app.models.lesion import Lesion


class User(TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(check_in("role", Role), name="role"),
        CheckConstraint(
            "skin_type IS NULL OR skin_type IN ('I','II','III','IV','V','VI')", name="skin_type"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(100))
    full_name: Mapped[str] = mapped_column(String(120))
    date_of_birth: Mapped[date | None] = mapped_column(Date)
    skin_type: Mapped[str | None] = mapped_column(String(3))
    location: Mapped[str | None] = mapped_column(String(120))
    bio: Mapped[str | None] = mapped_column(Text)
    role: Mapped[str] = mapped_column(String(20), default=Role.user.value, server_default="user")

    lesions: Mapped[list[Lesion]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )
