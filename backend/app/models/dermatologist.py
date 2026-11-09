from __future__ import annotations

from sqlalchemy import Boolean, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class Dermatologist(TimestampMixin, Base):
    __tablename__ = "dermatologists"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    title: Mapped[str] = mapped_column(String(120))
    specialty: Mapped[str] = mapped_column(String(120), index=True)
    clinic_name: Mapped[str] = mapped_column(String(160))
    city: Mapped[str] = mapped_column(String(80), index=True)
    address: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str] = mapped_column(String(40))
    timezone: Mapped[str] = mapped_column(String(64), default="UTC")
    rating: Mapped[float] = mapped_column(Float, default=0.0)
    review_count: Mapped[int] = mapped_column(Integer, default=0)
    languages: Mapped[list[str]] = mapped_column(JSONB, default=list)
    accepts_new_patients: Mapped[bool] = mapped_column(Boolean, default=True)
    bio: Mapped[str] = mapped_column(Text, default="")
    is_sample: Mapped[bool] = mapped_column(Boolean, default=True)
