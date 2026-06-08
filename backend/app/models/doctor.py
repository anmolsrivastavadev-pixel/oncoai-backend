from sqlalchemy import Column, Integer, String, Float, Boolean, Text
from sqlalchemy.orm import relationship
from app.db.session import Base

class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    specialty = Column(String, index=True)
    location = Column(String, index=True)
    rating = Column(Float, default=5.0)
    image_url = Column(String, nullable=True)
    experience = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    lat = Column(Float, nullable=True)
    lon = Column(Float, nullable=True)
    
    bio = Column(Text, nullable=True)
    qualifications = Column(String, nullable=True)
    languages = Column(String, nullable=True)
    consultation_fee = Column(Float, default=0.0)
    is_verified = Column(Boolean, default=False)
    hospital_name = Column(String, index=True, nullable=True)
    google_place_id = Column(String, unique=True, index=True, nullable=True)

    # Use string reference "Appointment" to avoid circular imports
    appointments = relationship("Appointment", back_populates="doctor", cascade="all, delete-orphan")
