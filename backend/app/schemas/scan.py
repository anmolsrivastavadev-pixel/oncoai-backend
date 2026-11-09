from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.models.enums import BodyLocation, ConcernLevel
from app.schemas.common import DisclaimerMixin, ORMModel, UTCDateTime


class Symptoms(BaseModel):
    itching: bool = False
    bleeding: bool = False
    pain: bool = False
    changed_size: bool = False
    changed_color: bool = False
    changed_shape: bool = False
    new_spot: bool = False
    notes: str | None = Field(default=None, max_length=1000)


class Quality(BaseModel):
    ok: bool
    blur_score: float
    brightness: float
    contrast: float
    issues: list[str]


class Features(BaseModel):
    asymmetry: float = Field(ge=0, le=100)
    border_irregularity: float = Field(ge=0, le=100)
    color_variation: float = Field(ge=0, le=100)
    diameter_px: float
    diameter_relative: float = Field(ge=0, le=100)
    color_count: int


class ModelMeta(BaseModel):
    name: str
    kind: Literal["vit", "heuristic"]
    version: str


class ScanSummary(BaseModel):
    id: int
    lesion_id: int
    created_at: UTCDateTime
    concern_level: ConcernLevel
    concern_score: float
    thumbnail_url: str
    headline: str


class ScanOut(ScanSummary, DisclaimerMixin):
    image_url: str
    quality: Quality
    features: Features
    observations: list[str]
    recommendations: list[str]
    symptoms: Symptoms | None
    model: ModelMeta


class LesionCreate(BaseModel):
    label: str = Field(min_length=1, max_length=80)
    body_location: BodyLocation
    notes: str | None = Field(default=None, max_length=2000)


class LesionUpdate(BaseModel):
    label: str | None = Field(default=None, min_length=1, max_length=80)
    body_location: BodyLocation | None = None
    notes: str | None = Field(default=None, max_length=2000)


class LesionOut(ORMModel):
    id: int
    label: str
    body_location: BodyLocation
    notes: str | None
    created_at: UTCDateTime
    scan_count: int
    latest_concern: ConcernLevel | None
    latest_scan_at: UTCDateTime | None
    thumbnail_url: str | None


class LesionDetail(LesionOut):
    scans: list[ScanSummary]
