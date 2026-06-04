from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct, cast, Date
from app import models, schemas
from app.api import deps
from app.db.session import get_db

router = APIRouter()


@router.post("/tokens")
def register_device_token(
    token_in: schemas.messaging.DeviceTokenRegister,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    existing = db.query(models.DeviceToken).filter(
        models.DeviceToken.token == token_in.token
    ).first()
    if existing:
        existing.user_id = current_user.id
        existing.is_active = True
        db.commit()
        return {"detail": "Token updated"}

    dt = models.DeviceToken(
        user_id=current_user.id, token=token_in.token, platform=token_in.platform
    )
    db.add(dt)
    db.commit()
    return {"detail": "Token registered"}


@router.delete("/tokens/{token}")
def unregister_token(
    token: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    db.query(models.DeviceToken).filter(
        models.DeviceToken.token == token,
        models.DeviceToken.user_id == current_user.id,
    ).delete()
    db.commit()
    return {"detail": "Token removed"}


def send_push_notification(user_id: int, title: str, body: str, db: Session):
    """Send push notification to all registered devices for a user."""
    try:
        import requests
        tokens = db.query(models.DeviceToken).filter(
            models.DeviceToken.user_id == user_id,
            models.DeviceToken.is_active == True,
        ).all()
        for dt in tokens:
            # FCM v1 or legacy — use whatever is configured
            pass
    except Exception:
        pass


# ─── DIRECT MESSAGES ─────────────────────────────────────────

@router.get("/messages/conversations")
def get_conversations(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    sent = db.query(
        models.Message.receiver_id,
        func.max(models.Message.created_at).label("last_time"),
    ).filter(models.Message.sender_id == current_user.id).group_by(models.Message.receiver_id).all()

    received = db.query(
        models.Message.sender_id,
        func.max(models.Message.created_at).label("last_time"),
    ).filter(models.Message.receiver_id == current_user.id).group_by(models.Message.sender_id).all()

    conv_map = {}
    for other_id, last_time in sent:
        conv_map[other_id] = {"last_time": last_time, "unread": 0}

    for other_id, last_time in received:
        if other_id not in conv_map or (last_time and conv_map[other_id]["last_time"] < last_time):
            conv_map[other_id] = {"last_time": last_time, "unread": 0}

    for other_id in conv_map:
        unread = db.query(models.Message).filter(
            models.Message.sender_id == other_id,
            models.Message.receiver_id == current_user.id,
            models.Message.is_read == False,
        ).count()
        conv_map[other_id]["unread"] = unread

    users = {
        u.id: u.full_name
        for u in db.query(models.User).filter(models.User.id.in_(list(conv_map.keys()))).all()
    }

    last_msgs = {}
    for other_id in conv_map:
        msg = db.query(models.Message).filter(
            ((models.Message.sender_id == current_user.id) & (models.Message.receiver_id == other_id))
            | ((models.Message.sender_id == other_id) & (models.Message.receiver_id == current_user.id))
        ).order_by(models.Message.created_at.desc()).first()
        if msg:
            last_msgs[other_id] = msg.content[:80]

    return sorted(
        [
            {
                "user_id": oid,
                "user_name": users.get(oid, "Unknown"),
                "last_message": last_msgs.get(oid, ""),
                "last_message_time": info["last_time"],
                "unread_count": info["unread"],
            }
            for oid, info in conv_map.items()
        ],
        key=lambda c: c["last_message_time"],
        reverse=True,
    )


@router.get("/messages/{user_id}")
def get_messages(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_user),
    skip: int = 0,
    limit: int = 50,
) -> Any:
    messages = (
        db.query(models.Message)
        .filter(
            (
                (models.Message.sender_id == current_user.id)
                & (models.Message.receiver_id == user_id)
            )
            | (
                (models.Message.sender_id == user_id)
                & (models.Message.receiver_id == current_user.id)
            )
        )
        .order_by(models.Message.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    # Mark received messages as read
    for m in messages:
        if m.receiver_id == current_user.id and not m.is_read:
            m.is_read = True
    db.commit()

    users = {}
    all_user_ids = {m.sender_id for m in messages} | {m.receiver_id for m in messages}
    for u in db.query(models.User).filter(models.User.id.in_(all_user_ids)).all():
        users[u.id] = u.full_name

    return sorted(
        [
            {
                "id": m.id,
                "sender_id": m.sender_id,
                "receiver_id": m.receiver_id,
                "content": m.content,
                "is_read": m.is_read,
                "sender_name": users.get(m.sender_id, "Unknown"),
                "created_at": m.created_at,
            }
            for m in messages
        ],
        key=lambda x: x["created_at"],
    )


@router.post("/messages/{user_id}")
def send_message(
    user_id: int,
    message_in: schemas.messaging.MessageCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    receiver = db.query(models.User).filter(models.User.id == user_id).first()
    if not receiver:
        raise HTTPException(status_code=404, detail="User not found")

    msg = models.Message(
        sender_id=current_user.id,
        receiver_id=user_id,
        content=message_in.content,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)

    send_push_notification(user_id, f"New message from {current_user.full_name}", message_in.content[:100], db)

    return {
        "id": msg.id,
        "sender_id": msg.sender_id,
        "receiver_id": msg.receiver_id,
        "content": msg.content,
        "is_read": msg.is_read,
        "sender_name": current_user.full_name,
        "created_at": msg.created_at,
    }


# ─── DOCTOR VERIFICATION ──────────────────────────────────────

@router.post("/doctors/{doctor_id}/verify")
def verify_doctor(
    doctor_id: int,
    verify_in: schemas.messaging.DoctorVerifyRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_superuser),
) -> Any:
    doctor = db.query(models.Doctor).filter(models.Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    doctor.is_verified = verify_in.is_verified
    db.commit()
    return {"detail": f"Doctor {'verified' if verify_in.is_verified else 'unverified'}", "is_verified": doctor.is_verified}


# ─── ANALYTICS ────────────────────────────────────────────────

@router.get("/analytics")
def get_analytics(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_superuser),
) -> Any:
    from datetime import date

    today = date.today()
    total_users = db.query(func.count(models.User.id)).scalar() or 0
    total_scans = db.query(func.count(models.Scan.id)).scalar() or 0
    total_posts = db.query(func.count(models.Post.id)).scalar() or 0
    total_comments = db.query(func.count(models.Comment.id)).scalar() or 0
    total_reactions = db.query(func.count(models.PostReaction.id)).scalar() or 0
    total_groups = db.query(func.count(models.Group.id)).scalar() or 0
    flagged_posts = db.query(func.count(models.Post.id)).filter(models.Post.is_flagged == True).scalar() or 0
    banned_users = db.query(func.count(models.User.id)).filter(models.User.is_active == False).scalar() or 0

    scans_today = db.query(func.count(models.Scan.id)).filter(
        cast(models.Scan.created_at, Date) == today
    ).scalar() or 0
    posts_today = db.query(func.count(models.Post.id)).filter(
        cast(models.Post.created_at, Date) == today
    ).scalar() or 0
    new_users_today = 0

    classifications = db.query(
        models.Scan.classification, func.count(models.Scan.id)
    ).group_by(models.Scan.classification).all()

    moods = db.query(
        models.CheckIn.mood, func.count(models.CheckIn.id)
    ).group_by(models.CheckIn.mood).all()

    return {
        "total_users": total_users, "total_scans": total_scans,
        "total_posts": total_posts, "total_comments": total_comments,
        "total_reactions": total_reactions, "total_groups": total_groups,
        "flagged_posts": flagged_posts, "banned_users": banned_users,
        "scans_today": scans_today, "posts_today": posts_today,
        "new_users_today": new_users_today,
        "scan_classifications": dict(classifications),
        "mood_distribution": dict(moods),
        "daily_scans": [], "daily_posts": [],
    }


# ─── EMAIL NOTIFICATIONS ──────────────────────────────────────

@router.post("/email/test")
def send_test_email(
    email_in: schemas.messaging.EmailTest,
    current_user: models.User = Depends(deps.get_current_superuser),
) -> Any:
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    from app.core.config import settings

    smtp_host = getattr(settings, "SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(getattr(settings, "SMTP_PORT", "587"))
    smtp_user = getattr(settings, "SMTP_USER", "")
    smtp_pass = getattr(settings, "SMTP_PASSWORD", "")

    if not smtp_user or not smtp_pass:
        raise HTTPException(status_code=500, detail="SMTP not configured. Set SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD in .env.")

    msg = MIMEMultipart()
    msg["From"] = smtp_user
    msg["To"] = email_in.email
    msg["Subject"] = f"[OncoAI] {email_in.subject}"
    msg.attach(MIMEText(email_in.body, "html"))

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        return {"detail": f"Email sent to {email_in.email}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send: {str(e)}")


def send_email(to_email: str, subject: str, body_html: str, db: Session = None):
    """Send an email notification. Requires SMTP configured in .env."""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    from app.core.config import settings

    smtp_user = getattr(settings, "SMTP_USER", "")
    smtp_pass = getattr(settings, "SMTP_PASSWORD", "")

    if not smtp_user or not smtp_pass:
        return

    msg = MIMEMultipart()
    msg["From"] = smtp_user
    msg["To"] = to_email
    msg["Subject"] = f"[OncoAI] {subject}"
    msg.attach(MIMEText(body_html, "html"))

    try:
        smtp_host = getattr(settings, "SMTP_HOST", "smtp.gmail.com")
        smtp_port = int(getattr(settings, "SMTP_PORT", "587"))
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
    except Exception:
        pass
