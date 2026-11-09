from __future__ import annotations

import json
from typing import Annotated, Literal

from fastapi import Depends, File, Form, HTTPException, Query, Response, UploadFile, status
from pydantic import ValidationError
from sqlalchemy import func, select

from app.api.deps import DB, CurrentUser, Paging, scan_rate_limit
from app.api.router import SlashRouter
from app.core.config import settings
from app.models import Scan
from app.schemas.common import Page
from app.schemas.scan import ScanOut, ScanSummary, Symptoms
from app.services import scan_service, storage

router = SlashRouter(prefix="/scans", tags=["scans"])

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "application/octet-stream"}


def _parse_symptoms(raw: str | None) -> Symptoms | None:
    if raw is None or not raw.strip():
        return None
    try:
        return Symptoms.model_validate(json.loads(raw))
    except (json.JSONDecodeError, ValidationError) as exc:
        raise HTTPException(
            422, "symptoms must be a JSON object matching Symptoms."
        ) from exc


@router.post(
    "/",
    response_model=ScanOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(scan_rate_limit)],
)
def create_scan(
    user: CurrentUser,
    db: DB,
    image: Annotated[UploadFile, File(description="JPEG, PNG or WebP photo, max 10 MB")],
    lesion_id: Annotated[int | None, Form()] = None,
    symptoms: Annotated[str | None, Form(max_length=4000)] = None,
) -> ScanOut:
    if image.content_type and image.content_type.lower() not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Unsupported image type. Upload a JPEG, PNG or WebP photo."
        )
    parsed = _parse_symptoms(symptoms)
    raw = image.file.read(settings.MAX_UPLOAD_BYTES + 1)
    scan = scan_service.create_scan(db, user.id, raw, lesion_id, parsed)
    return scan_service.to_out(scan)


@router.get("/", response_model=Page[ScanSummary])
def list_scans(
    user: CurrentUser, db: DB, paging: Paging, lesion_id: int | None = None
) -> Page[ScanSummary]:
    condition = [Scan.user_id == user.id]
    if lesion_id is not None:
        condition.append(Scan.lesion_id == lesion_id)
    total = db.scalar(select(func.count(Scan.id)).where(*condition)) or 0
    scans = db.scalars(
        select(Scan)
        .where(*condition)
        .order_by(Scan.created_at.desc(), Scan.id.desc())
        .limit(paging.limit)
        .offset(paging.offset)
    ).all()
    return Page(items=[scan_service.to_summary(s) for s in scans], total=total)


@router.get("/{scan_id}", response_model=ScanOut)
def get_scan(scan_id: int, user: CurrentUser, db: DB) -> ScanOut:
    return scan_service.to_out(scan_service.get_owned_scan(db, user.id, scan_id))


@router.get(
    "/{scan_id}/image",
    response_class=Response,
    responses={200: {"content": {"image/jpeg": {}}}},
)
def get_scan_image(
    scan_id: int,
    user: CurrentUser,
    db: DB,
    variant: Annotated[Literal["full", "thumb"], Query()] = "full",
) -> Response:
    scan = scan_service.get_owned_scan(db, user.id, scan_id)
    path = scan.thumb_path if variant == "thumb" else scan.image_path
    try:
        data = storage.read_image(path)
    except FileNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Image not found") from exc
    return Response(
        content=data,
        media_type="image/jpeg",
        headers={"Cache-Control": "private, no-store", "Content-Disposition": "inline"},
    )


@router.delete("/{scan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scan(scan_id: int, user: CurrentUser, db: DB) -> Response:
    scan = scan_service.get_owned_scan(db, user.id, scan_id)
    paths = [scan.image_path, scan.thumb_path]
    db.delete(scan)
    db.commit()
    storage.delete_files(paths)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
