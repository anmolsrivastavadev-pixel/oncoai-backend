from __future__ import annotations

from fastapi import Response, status
from sqlalchemy import func, select

from app.api.deps import DB, CurrentUser, Paging
from app.api.router import SlashRouter
from app.models import Lesion, Scan
from app.schemas.common import Page
from app.schemas.scan import LesionCreate, LesionDetail, LesionOut, LesionUpdate
from app.services import storage
from app.services.scan_service import get_owned_lesion, lesion_detail, lesion_out

router = SlashRouter(prefix="/lesions", tags=["lesions"])


@router.get("/", response_model=Page[LesionOut])
def list_lesions(user: CurrentUser, db: DB, paging: Paging) -> Page[LesionOut]:
    total = db.scalar(select(func.count(Lesion.id)).where(Lesion.user_id == user.id)) or 0
    lesions = db.scalars(
        select(Lesion)
        .where(Lesion.user_id == user.id)
        .order_by(Lesion.created_at.desc(), Lesion.id.desc())
        .limit(paging.limit)
        .offset(paging.offset)
    ).all()
    return Page(items=[lesion_out(db, lesion) for lesion in lesions], total=total)


@router.post("/", response_model=LesionOut, status_code=status.HTTP_201_CREATED)
def create_lesion(payload: LesionCreate, user: CurrentUser, db: DB) -> LesionOut:
    lesion = Lesion(
        user_id=user.id,
        label=payload.label.strip(),
        body_location=payload.body_location.value,
        notes=payload.notes,
    )
    db.add(lesion)
    db.commit()
    db.refresh(lesion)
    return lesion_out(db, lesion)


@router.get("/{lesion_id}", response_model=LesionDetail)
def get_lesion(lesion_id: int, user: CurrentUser, db: DB) -> LesionDetail:
    return lesion_detail(db, get_owned_lesion(db, user.id, lesion_id))


@router.patch("/{lesion_id}", response_model=LesionOut)
def update_lesion(lesion_id: int, payload: LesionUpdate, user: CurrentUser, db: DB) -> LesionOut:
    lesion = get_owned_lesion(db, user.id, lesion_id)
    data = payload.model_dump(exclude_unset=True)
    if data.get("label"):
        lesion.label = data["label"].strip()
    if data.get("body_location"):
        lesion.body_location = data["body_location"].value
    if "notes" in data:
        lesion.notes = data["notes"]
    db.commit()
    db.refresh(lesion)
    return lesion_out(db, lesion)


@router.delete("/{lesion_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lesion(lesion_id: int, user: CurrentUser, db: DB) -> Response:
    lesion = get_owned_lesion(db, user.id, lesion_id)
    rows = db.execute(select(Scan.image_path, Scan.thumb_path).where(Scan.lesion_id == lesion.id)).all()
    db.delete(lesion)
    db.commit()
    storage.delete_files([path for row in rows for path in row])
    return Response(status_code=status.HTTP_204_NO_CONTENT)
