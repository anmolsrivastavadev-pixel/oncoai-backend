from pydantic import BaseModel
from typing import Optional

class DoctorBase(BaseModel):
    name: str
    specialty: str
    location: str
    rating: float
    image_url: Optional[str] = None
    experience: Optional[str] = None
    phone: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    
    bio: Optional[str] = None
    qualifications: Optional[str] = None
    languages: Optional[str] = None
    consultation_fee: Optional[float] = 0.0
    is_verified: Optional[bool] = False
    hospital_name: Optional[str] = None
    google_place_id: Optional[str] = None

class DoctorCreate(DoctorBase):
    pass

class Doctor(DoctorBase):
    id: int

    class Config:
        from_attributes = True
