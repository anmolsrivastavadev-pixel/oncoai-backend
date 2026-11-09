from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import CheckConstraint, Float, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import ConcernLevel, check_in

if TYPE_CHECKING:
    from app.models.lesion import Lesion


class Scan(TimestampMixin, Base):
    __tablename__ = "scans"
    __table_args__ = (
        CheckConstraint(check_in("concern_level", ConcernLevel), name="concern_level"),
        CheckConstraint("concern_score >= 0 AND concern_score <= 100", name="concern_score"),
        Index("ix_scans_user_created", "user_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    lesion_id: Mapped[int] = mapped_column(ForeignKey("lesions.id", ondelete="CASCADE"), index=True)

    # Paths relative to settings.UPLOAD_DIR; never exposed to clients.
    image_path: Mapped[str] = mapped_column(String(255))
    thumb_path: Mapped[str] = mapped_column(String(255))

    concern_level: Mapped[str] = mapped_column(String(16))
    concern_score: Mapped[float] = mapped_column(Float)
    headline: Mapped[str] = mapped_column(String(255))
    quality: Mapped[dict[str, Any]] = mapped_column(JSONB)
    features: Mapped[dict[str, Any]] = mapped_column(JSONB)
    observations: Mapped[list[str]] = mapped_column(JSONB)
    recommendations: Mapped[list[str]] = mapped_column(JSONB)
    symptoms: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    model_name: Mapped[str] = mapped_column(String(120))
    model_kind: Mapped[str] = mapped_column(String(16))
    model_version: Mapped[str] = mapped_column(String(64))
    # Internal audit trail (raw class probabilities, component scores). NEVER serialised
    # into API responses.
    analysis_audit: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)

    lesion: Mapped[Lesion] = relationship(back_populates="scans")
