from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, schemas
from app.api import deps
from app.db.session import get_db

router = APIRouter()


@router.get("")
def get_notifications(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_user),
    skip: int = 0,
    limit: int = 50,
) -> Any:
    notifications = (
        db.query(models.Notification)
        .filter(models.Notification.user_id == current_user.id)
        .order_by(models.Notification.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [
        {
            "id": n.id,
            "type": n.type,
            "message": n.message,
            "is_read": n.is_read,
            "related_entity_type": n.related_entity_type,
            "related_entity_id": n.related_entity_id,
            "created_at": n.created_at,
        }
        for n in notifications
    ]


@router.get("/unread-count")
def unread_count(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    count = (
        db.query(models.Notification)
        .filter(
            models.Notification.user_id == current_user.id,
            models.Notification.is_read == False,
        )
        .count()
    )
    return {"count": count}


@router.patch("/{notification_id}/read")
def mark_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    notification = (
        db.query(models.Notification)
        .filter(
            models.Notification.id == notification_id,
            models.Notification.user_id == current_user.id,
        )
        .first()
    )
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    notification.is_read = True
    db.commit()
    return {"detail": "Marked as read"}


def create_notification(
    db: Session,
    user_id: int,
    type: str,
    message: str,
    entity_type: str = None,
    entity_id: int = None,
):
    notification = models.Notification(
        user_id=user_id,
        type=type,
        message=message,
        related_entity_type=entity_type,
        related_entity_id=entity_id,
    )
    db.add(notification)
    return notification
