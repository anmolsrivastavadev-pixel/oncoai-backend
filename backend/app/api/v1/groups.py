from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, schemas
from app.api import deps
from app.db.session import get_db

router = APIRouter()


@router.get("")
def list_groups(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    groups = db.query(models.Group).order_by(models.Group.name).all()
    user_memberships = {
        m.group_id: m
        for m in db.query(models.GroupMember)
        .filter(models.GroupMember.user_id == current_user.id)
        .all()
    }
    return [
        {
            "id": g.id,
            "name": g.name,
            "slug": g.slug,
            "description": g.description,
            "icon": g.icon,
            "is_private": g.is_private,
            "created_at": g.created_at,
            "member_count": len(g.members),
            "is_member": g.id in user_memberships,
        }
        for g in groups
    ]


@router.get("/{group_slug}")
def get_group(
    group_slug: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    group = db.query(models.Group).filter(models.Group.slug == group_slug).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    user_member = (
        db.query(models.GroupMember)
        .filter(
            models.GroupMember.group_id == group.id,
            models.GroupMember.user_id == current_user.id,
        )
        .first()
    )

    members = [
        {
            "id": m.id,
            "user_id": m.user_id,
            "full_name": m.user.full_name if m.user else "Unknown",
            "role": m.role,
            "joined_at": m.joined_at,
        }
        for m in group.members
    ]

    return {
        "id": group.id,
        "name": group.name,
        "slug": group.slug,
        "description": group.description,
        "icon": group.icon,
        "is_private": group.is_private,
        "created_at": group.created_at,
        "member_count": len(group.members),
        "is_member": user_member is not None,
        "members": members,
    }


@router.post("/{group_slug}/join")
def join_group(
    group_slug: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    group = db.query(models.Group).filter(models.Group.slug == group_slug).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    existing = (
        db.query(models.GroupMember)
        .filter(
            models.GroupMember.group_id == group.id,
            models.GroupMember.user_id == current_user.id,
        )
        .first()
    )
    if existing:
        return {"detail": "Already a member"}

    member = models.GroupMember(group_id=group.id, user_id=current_user.id)
    db.add(member)
    db.commit()
    return {"detail": "Joined group"}


@router.post("/{group_slug}/leave")
def leave_group(
    group_slug: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    group = db.query(models.Group).filter(models.Group.slug == group_slug).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    member = (
        db.query(models.GroupMember)
        .filter(
            models.GroupMember.group_id == group.id,
            models.GroupMember.user_id == current_user.id,
        )
        .first()
    )
    if not member:
        raise HTTPException(status_code=404, detail="Not a member")
    db.delete(member)
    db.commit()
    return {"detail": "Left group"}


@router.get("/{group_slug}/posts")
def get_group_posts(
    group_slug: str,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 20,
) -> Any:
    group = db.query(models.Group).filter(models.Group.slug == group_slug).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    posts = (
        db.query(models.Post)
        .filter(
            models.Post.group_id == group.id,
            models.Post.is_hidden == False,
        )
        .order_by(models.Post.pinned.desc(), models.Post.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    results = []
    for p in posts:
        reaction_counts = {}
        for r in p.reactions:
            reaction_counts[r.reaction_type] = reaction_counts.get(r.reaction_type, 0) + 1
        results.append({
            "id": p.id,
            "title": p.title,
            "content": p.content,
            "category": p.category,
            "author_name": "Community Member" if p.is_anonymous else (p.author.full_name if p.author else None),
            "user_id": None if p.is_anonymous else p.user_id,
            "is_anonymous": p.is_anonymous,
            "comment_count": len(p.comments),
            "reaction_counts": reaction_counts,
            "created_at": p.created_at,
            "pinned": p.pinned,
            "is_flagged": p.is_flagged,
            "group_id": p.group_id,
        })

    return results
