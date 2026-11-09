"""Scan creation and serialisation helpers (shared by scans, lesions and tracking).

``create_scan`` is synchronous and CPU-heavy; it is called from a sync FastAPI endpoint,
which Starlette runs in its worker threadpool so the event loop is never blocked.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.ml.analyzer import AnalysisResult
from app.ml.concern import ConcernReport, build_report
from app.ml.registry import get_analyzer
from app.models import Lesion, Scan
from app.models.enums import BodyLocation
from app.schemas.scan import (
    Features,
    LesionDetail,
    LesionOut,
    ModelMeta,
    Quality,
    ScanOut,
    ScanSummary,
    Symptoms,
)
from app.services import storage

logger = logging.getLogger(__name__)


def image_url(scan_id: int) -> str:
    return f"{settings.API_V1_PREFIX}/scans/{scan_id}/image"


def thumbnail_url(scan_id: int) -> str:
    return f"{image_url(scan_id)}?variant=thumb"


def to_summary(scan: Scan) -> ScanSummary:
    return ScanSummary(
        id=scan.id,
        lesion_id=scan.lesion_id,
        created_at=scan.created_at,
        concern_level=scan.concern_level,
        concern_score=scan.concern_score,
        thumbnail_url=thumbnail_url(scan.id),
        headline=scan.headline,
    )


def to_out(scan: Scan) -> ScanOut:
    # NOTE: analysis_audit (class probabilities) is deliberately not part of ScanOut.
    return ScanOut(
        **to_summary(scan).model_dump(),
        image_url=image_url(scan.id),
        quality=Quality.model_validate(scan.quality),
        features=Features.model_validate(scan.features),
        observations=list(scan.observations),
        recommendations=list(scan.recommendations),
        symptoms=Symptoms.model_validate(scan.symptoms) if scan.symptoms else None,
        model=ModelMeta(name=scan.model_name, kind=scan.model_kind, version=scan.model_version),  # type: ignore[arg-type]
    )


def lesion_out(db: Session, lesion: Lesion) -> LesionOut:
    count = db.scalar(select(func.count(Scan.id)).where(Scan.lesion_id == lesion.id)) or 0
    latest = db.scalar(
        select(Scan).where(Scan.lesion_id == lesion.id).order_by(Scan.created_at.desc(), Scan.id.desc()).limit(1)
    )
    return LesionOut(
        id=lesion.id,
        label=lesion.label,
        body_location=lesion.body_location,
        notes=lesion.notes,
        created_at=lesion.created_at,
        scan_count=count,
        latest_concern=latest.concern_level if latest else None,
        latest_scan_at=latest.created_at if latest else None,
        thumbnail_url=thumbnail_url(latest.id) if latest else None,
    )


def lesion_detail(db: Session, lesion: Lesion) -> LesionDetail:
    scans = db.scalars(
        select(Scan).where(Scan.lesion_id == lesion.id).order_by(Scan.created_at.desc(), Scan.id.desc())
    ).all()
    return LesionDetail(**lesion_out(db, lesion).model_dump(), scans=[to_summary(s) for s in scans])


def get_owned_lesion(db: Session, user_id: int, lesion_id: int) -> Lesion:
    lesion = db.get(Lesion, lesion_id)
    if lesion is None or lesion.user_id != user_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Lesion not found")
    return lesion


def get_owned_scan(db: Session, user_id: int, scan_id: int) -> Scan:
    scan = db.get(Scan, scan_id)
    if scan is None or scan.user_id != user_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Scan not found")
    return scan


def _auto_lesion(db: Session, user_id: int) -> Lesion:
    count = db.scalar(select(func.count(Lesion.id)).where(Lesion.user_id == user_id)) or 0
    lesion = Lesion(user_id=user_id, label=f"Spot {count + 1}", body_location=BodyLocation.other.value)
    db.add(lesion)
    db.flush()
    return lesion


def _analyze(processed: storage.ProcessedImage, symptoms: dict[str, Any] | None) -> tuple[AnalysisResult, ConcernReport]:
    analyzer = get_analyzer()
    result = analyzer.analyze(processed.image)
    return result, build_report(result, symptoms)


def create_scan(
    db: Session,
    user_id: int,
    raw: bytes,
    lesion_id: int | None,
    symptoms: Symptoms | None,
) -> Scan:
    lesion = get_owned_lesion(db, user_id, lesion_id) if lesion_id is not None else None

    started = time.perf_counter()
    try:
        processed = storage.process_upload(raw)
    except storage.ImageValidationError as exc:
        raise HTTPException(exc.status_code, str(exc)) from exc
    symptom_dict = symptoms.model_dump() if symptoms else None
    result, report = _analyze(processed, symptom_dict)
    analysed = time.perf_counter()

    stored = storage.save_scan_images(user_id, processed)
    try:
        if lesion is None:
            lesion = _auto_lesion(db, user_id)
        scan = Scan(
            user_id=user_id,
            lesion_id=lesion.id,
            image_path=stored.image_path,
            thumb_path=stored.thumb_path,
            concern_level=report.level.value,
            concern_score=report.score,
            headline=report.headline,
            quality=result.cv.quality.to_dict(),
            features=result.cv.features.to_dict(),
            observations=report.observations,
            recommendations=report.recommendations,
            symptoms=symptom_dict,
            model_name=result.info.name,
            model_kind=result.info.kind,
            model_version=result.info.version,
            analysis_audit=report.audit,
        )
        db.add(scan)
        db.commit()
    except Exception:
        db.rollback()
        storage.delete_files([stored.image_path, stored.thumb_path])
        raise
    db.refresh(scan)
    logger.info(
        "scan created",
        extra={
            "scan_id": scan.id,
            "kind": result.info.kind,
            "concern_level": scan.concern_level,
            "analysis_ms": round((analysed - started) * 1000),
        },
    )
    return scan
