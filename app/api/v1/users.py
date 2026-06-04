from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, schemas
from app.api import deps
from app.db.session import get_db

router = APIRouter()


@router.get("/profile")
def get_my_profile(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    user = db.query(models.User).filter(models.User.id == current_user.id).first()
    return {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "bio": user.bio,
        "support_badges": user.support_badges,
        "profile_photo_url": user.profile_photo_url,
        "is_superuser": user.is_superuser,
        "strike_count": user.strike_count,
        "post_count": len(user.posts),
        "comment_count": len(user.comments),
        "joined_date": user.posts[0].created_at.isoformat() if user.posts else None,
    }


@router.patch("/profile")
def update_profile(
    *,
    db: Session = Depends(get_db),
    profile_in: dict,
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    user = db.query(models.User).filter(models.User.id == current_user.id).first()
    allowed = ["bio", "support_badges", "full_name", "profile_photo_url"]
    for field in allowed:
        if field in profile_in:
            setattr(user, field, profile_in[field])
    db.commit()
    return {"detail": "Profile updated"}


@router.get("/milestones")
def get_milestones(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    post_count = len(current_user.posts)
    scan_count = len(current_user.scans)
    comment_count = len(current_user.comments)

    milestones = [
        {
            "key": "first_post",
            "label": "First Voice",
            "description": "Created your first community post",
            "achieved": post_count >= 1,
            "progress": min(1.0, post_count / 1),
        },
        {
            "key": "ten_posts",
            "label": "Community Contributor",
            "description": "Published 10 posts",
            "achieved": post_count >= 10,
            "progress": min(1.0, post_count / 10),
        },
        {
            "key": "fifty_posts",
            "label": "Community Leader",
            "description": "Published 50 posts",
            "achieved": post_count >= 50,
            "progress": min(1.0, post_count / 50),
        },
        {
            "key": "first_scan",
            "label": "First Insight",
            "description": "Completed your first skin scan",
            "achieved": scan_count >= 1,
            "progress": min(1.0, scan_count / 1),
        },
        {
            "key": "ten_scans",
            "label": "Diligent Monitor",
            "description": "Completed 10 skin scans",
            "achieved": scan_count >= 10,
            "progress": min(1.0, scan_count / 10),
        },
        {
            "key": "supportive",
            "label": "Supportive Soul",
            "description": "Left 25 comments supporting others",
            "achieved": comment_count >= 25,
            "progress": min(1.0, comment_count / 25),
        },
    ]
    return milestones
