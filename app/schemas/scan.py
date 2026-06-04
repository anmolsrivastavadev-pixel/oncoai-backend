from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict


class ScanBase(BaseModel):
    filename: str
    classification: str
    confidence: float
    guidance: str


class ScanCreate(ScanBase):
    pass


class Scan(ScanBase):
    id: int
    created_at: datetime
    user_id: int
    quality_score: Optional[float] = None
    asymmetry_score: Optional[float] = None
    border_score: Optional[float] = None
    color_score: Optional[float] = None
    diameter_mm: Optional[float] = None
    feature_details: Optional[str] = None

    class Config:
        from_attributes = True


class ScanComparison(BaseModel):
    scan_id_1: int
    scan_id_2: int
    similarity: float
    change_detected: bool
    notes: str
