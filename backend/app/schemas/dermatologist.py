from __future__ import annotations

from pydantic import BaseModel

from app.schemas.common import ORMModel


class DermatologistOut(ORMModel):
    id: int
    name: str
    title: str
    specialty: str
    clinic_name: str
    city: str
    address: str
    phone: str
    timezone: str
    rating: float
    review_count: int
    languages: list[str]
    accepts_new_patients: bool
    bio: str
    is_sample: bool


class AvailabilityOut(BaseModel):
    date: str
    slots: list[str]
