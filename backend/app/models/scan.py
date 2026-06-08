from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base


class Scan(Base):
    __tablename__ = "scans"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    classification = Column(String, index=True)
    confidence = Column(Float)
    guidance = Column(String)
    quality_score = Column(Float, nullable=True)
    asymmetry_score = Column(Float, nullable=True)
    border_score = Column(Float, nullable=True)
    color_score = Column(Float, nullable=True)
    diameter_mm = Column(Float, nullable=True)
    feature_details = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="scans")
