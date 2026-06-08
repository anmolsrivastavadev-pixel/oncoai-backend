from typing import Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app import models, schemas
from app.api import deps
from app.api.v1.messaging import send_email
from app.db.session import get_db

router = APIRouter()


@router.get("/queue")
def list_flagged_posts(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: models.User = Depends(deps.get_current_superuser),
) -> Any:
    query = db.query(models.Post).filter(models.Post.is_flagged == True)
    total = query.count()
    posts = (
        query.order_by(models.Post.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [
        {
            "id": p.id,
            "title": p.title,
            "content": p.content,
            "category": p.category,
            "author_name": p.author.full_name if p.author else None,
            "author_email": p.author.email if p.author else None,
            "author_id": p.user_id,
            "is_flagged": p.is_flagged,
            "flag_reason": p.flag_reason,
            "flagged_by": p.flagged_by,
            "is_hidden": p.is_hidden,
            "pinned": p.pinned,
            "created_at": p.created_at,
            "comment_count": len(p.comments),
        }
        for p in posts
    ]


@router.get("/queue/stats")
def moderation_stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_superuser),
) -> Any:
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    flagged_count = db.query(models.Post).filter(models.Post.is_flagged == True).count()
    hidden_count = db.query(models.Post).filter(models.Post.is_hidden == True).count()
    resolved_today = db.query(models.Post).filter(
        models.Post.is_flagged == False,
        models.Post.flagged_by != None,
        models.Post.created_at >= today_start,
    ).count()
    total_strikes = db.query(func.sum(models.User.strike_count)).scalar() or 0
    banned_users = db.query(models.User).filter(models.User.is_active == False).count()

    return {
        "flagged_posts": flagged_count,
        "hidden_posts": hidden_count,
        "resolved_today": resolved_today,
        "total_strikes_issued": total_strikes,
        "banned_users": banned_users,
        "active_users": db.query(models.User).filter(models.User.is_active == True).count(),
    }


@router.post("/posts/{post_id}/hide")
def toggle_hide_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_superuser),
) -> Any:
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    post.is_hidden = not post.is_hidden
    db.commit()
    return {"detail": f"Post {'hidden' if post.is_hidden else 'unhidden'}", "is_hidden": post.is_hidden}


@router.post("/posts/{post_id}/pin")
def toggle_pin_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_superuser),
) -> Any:
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    post.pinned = not post.pinned
    db.commit()
    return {"detail": f"Post {'pinned' if post.pinned else 'unpinned'}", "pinned": post.pinned}


@router.post("/posts/{post_id}/dismiss-flag")
def dismiss_flag(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_superuser),
) -> Any:
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    post.is_flagged = False
    post.flag_reason = None
    post.flagged_by = None
    db.commit()
    return {"detail": "Flag dismissed"}


@router.post("/users/{user_id}/strike")
def issue_strike(
    user_id: int,
    strike_in: schemas.moderation.StrikeCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_superuser),
) -> Any:
    target_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    if target_user.is_superuser:
        raise HTTPException(status_code=403, detail="Cannot strike a superuser")

    target_user.strike_count += 1
    target_user.last_strike_at = datetime.utcnow()

    existing_notes = target_user.moderation_notes or ""
    target_user.moderation_notes = (
        f"{existing_notes}[Strike {target_user.strike_count}] {datetime.utcnow().isoformat()}: {strike_in.reason}\n"
    )

    if target_user.strike_count >= 3:
        target_user.is_active = False
        db.commit()
        send_email(target_user.email, "Account Suspended",
            f"<h2>Account Suspension Notice</h2><p>Your OncoAI account has been suspended due to repeated violations of our community guidelines.</p>"
            f"<p>This decision was made after 3 strikes for the following reasons:</p><pre>{target_user.moderation_notes}</pre>"
            f"<p>If you believe this is an error, please contact support.</p>")
        return {
            "detail": f"User banned. Strike {target_user.strike_count} of 3.",
            "strike_count": target_user.strike_count,
            "is_active": target_user.is_active,
        }

    if target_user.strike_count >= 2:
        target_user.is_active = True
        db.commit()
        return {
            "detail": f"User restricted from posting. Strike {target_user.strike_count} of 3. Next strike results in ban.",
            "strike_count": target_user.strike_count,
            "is_active": target_user.is_active,
        }

    db.commit()
    return {
        "detail": f"Warning issued. Strike {target_user.strike_count} of 3.",
        "strike_count": target_user.strike_count,
        "is_active": target_user.is_active,
    }


@router.post("/users/{user_id}/unban")
def unban_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_superuser),
) -> Any:
    target_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    target_user.is_active = True
    target_user.strike_count = 0
    target_user.moderation_notes = (
        f"{target_user.moderation_notes or ''}[Unbanned] {datetime.utcnow().isoformat()}: Reinstated by moderator\n"
    )
    db.commit()
    return {"detail": "User reinstated. Strikes reset."}


@router.get("/users")
def search_users(
    q: str = Query("", min_length=0),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_superuser),
) -> Any:
    query = db.query(models.User)
    if q:
        query = query.filter(
            models.User.full_name.ilike(f"%{q}%") | models.User.email.ilike(f"%{q}%")
        )
    users = query.order_by(models.User.strike_count.desc()).limit(50).all()
    return [
        {
            "id": u.id,
            "full_name": u.full_name,
            "email": u.email,
            "is_active": u.is_active,
            "is_superuser": u.is_superuser,
            "strike_count": u.strike_count,
            "last_strike_at": u.last_strike_at,
            "post_count": len(u.posts),
        }
        for u in users
    ]


@router.get("/posts/{post_id}")
def review_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_superuser),
) -> Any:
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return {
        "id": post.id,
        "title": post.title,
        "content": post.content,
        "category": post.category,
        "author_name": post.author.full_name if post.author else None,
        "author_email": post.author.email if post.author else None,
        "author_id": post.user_id,
        "is_flagged": post.is_flagged,
        "flag_reason": post.flag_reason,
        "flagged_by": post.flagged_by,
        "is_hidden": post.is_hidden,
        "pinned": post.pinned,
        "created_at": post.created_at,
        "comment_count": len(post.comments),
        "comments": [
            {
                "id": c.id,
                "content": c.content,
                "is_flagged": c.is_flagged,
                "author_name": c.author.full_name if c.author else None,
                "created_at": c.created_at,
            }
            for c in post.comments
        ],
    }
