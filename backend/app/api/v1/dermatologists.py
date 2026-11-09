from __future__ import annotations

from datetime import date as Date

from fastapi import HTTPException, Query, status
from sqlalchemy import func, or_, select

from app.api.deps import DB, CurrentUser, Paging
from app.api.router import SlashRouter
from app.models import Dermatologist
from app.schemas.common import Page
from app.schemas.dermatologist import AvailabilityOut, DermatologistOut
from app.services.booking import available_slots

router = SlashRouter(prefix="/dermatologists", tags=["dermatologists"])


def _like(value: str) -> str:
    escaped = value.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def get_dermatologist(db: DB, derm_id: int) -> Dermatologist:
    derm = db.get(Dermatologist, derm_id)
    if derm is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Dermatologist not found")
    return derm


@router.get("/", response_model=Page[DermatologistOut])
def search_dermatologists(
    _: CurrentUser,
    db: DB,
    paging: Paging,
    q: str | None = Query(default=None, max_length=100),
    city: str | None = Query(default=None, max_length=80),
    specialty: str | None = Query(default=None, max_length=120),
) -> Page[DermatologistOut]:
    conditions = []
    if q and q.strip():
        pattern = _like(q)
        conditions.append(
            or_(
                Dermatologist.name.ilike(pattern, escape="\\"),
                Dermatologist.clinic_name.ilike(pattern, escape="\\"),
                Dermatologist.specialty.ilike(pattern, escape="\\"),
                Dermatologist.city.ilike(pattern, escape="\\"),
            )
        )
    if city and city.strip():
        conditions.append(Dermatologist.city.ilike(_like(city), escape="\\"))
    if specialty and specialty.strip():
        conditions.append(Dermatologist.specialty.ilike(_like(specialty), escape="\\"))
    total = db.scalar(select(func.count(Dermatologist.id)).where(*conditions)) or 0
    rows = db.scalars(
        select(Dermatologist)
        .where(*conditions)
        .order_by(Dermatologist.rating.desc(), Dermatologist.id)
        .limit(paging.limit)
        .offset(paging.offset)
    ).all()
    return Page(items=[DermatologistOut.model_validate(r) for r in rows], total=total)


@router.get("/{derm_id}", response_model=DermatologistOut)
def read_dermatologist(derm_id: int, _: CurrentUser, db: DB) -> Dermatologist:
    return get_dermatologist(db, derm_id)


@router.get("/{derm_id}/availability", response_model=AvailabilityOut)
def availability(derm_id: int, _: CurrentUser, db: DB, date: Date) -> AvailabilityOut:
    derm = get_dermatologist(db, derm_id)
    return AvailabilityOut(date=date.isoformat(), slots=available_slots(db, derm, date))
