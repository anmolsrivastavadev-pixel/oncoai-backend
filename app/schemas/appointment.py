from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from .doctor import Doctor

class AppointmentBase(BaseModel):
    doctor_id: int
    appointment_datetime: datetime
    consultation_type: str = "in-person"
    notes: Optional[str] = None

class AppointmentCreate(AppointmentBase):
    pass

class AppointmentUpdate(BaseModel):
    status: Optional[str] = None
    appointment_datetime: Optional[datetime] = None
    notes: Optional[str] = None

class Appointment(AppointmentBase):
    id: int
    user_id: int
    status: str
    created_at: datetime
    doctor: Optional[Doctor] = None

    class Config:
        from_attributes = True
