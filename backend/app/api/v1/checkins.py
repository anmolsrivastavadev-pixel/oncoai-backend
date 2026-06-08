from typing import Any
from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, schemas
from app.api import deps
from app.db.session import get_db

router = APIRouter()

VALID_MOODS = ["hopeful", "grateful", "anxious", "tired", "determined", "okay", "struggling"]


@router.post("")
def create_checkin(
    *,
    checkin_in: schemas.checkin.CheckInCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    if checkin_in.mood not in VALID_MOODS:
        raise HTTPException(status_code=400, detail="Invalid mood")

    existing = (
        db.query(models.CheckIn)
        .filter(
            models.CheckIn.user_id == current_user.id,
        )
        .order_by(models.CheckIn.created_at.desc())
        .first()
    )
    if existing and existing.created_at.date() == date.today():
        return {
            "id": existing.id,
            "user_id": existing.user_id,
            "mood": existing.mood,
            "message": existing.message,
            "created_at": existing.created_at,
        }

    checkin = models.CheckIn(
        user_id=current_user.id,
        mood=checkin_in.mood,
        message=checkin_in.message,
    )
    db.add(checkin)
    db.commit()
    db.refresh(checkin)
    return {
        "id": checkin.id,
        "user_id": checkin.user_id,
        "mood": checkin.mood,
        "message": checkin.message,
        "created_at": checkin.created_at,
    }


@router.get("")
def get_checkins(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_user),
    skip: int = 0,
    limit: int = 30,
) -> Any:
    checkins = (
        db.query(models.CheckIn)
        .filter(models.CheckIn.user_id == current_user.id)
        .order_by(models.CheckIn.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [
        {
            "id": c.id,
            "user_id": c.user_id,
            "mood": c.mood,
            "message": c.message,
            "created_at": c.created_at,
        }
        for c in checkins
    ]


@router.get("/today")
def today_checkin(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    existing = (
        db.query(models.CheckIn)
        .filter(models.CheckIn.user_id == current_user.id)
        .order_by(models.CheckIn.created_at.desc())
        .first()
    )
    if existing and existing.created_at.date() == date.today():
        return {
            "checked_in": True,
            "mood": existing.mood,
            "message": existing.message,
            "created_at": existing.created_at,
        }
    return {"checked_in": False}
