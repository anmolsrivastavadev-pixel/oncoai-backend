from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app import models, schemas
from app.api import deps
from app.db.session import get_db
from app.api.v1.notifications import create_notification

router = APIRouter()

VALID_CATEGORIES = [
    "Journey Updates", "Emotional Support", "Scan Discussions",
    "Awareness", "Milestones", "Education",
]

VALID_REACTIONS = ["support", "strength", "hope", "helpful", "encouragement"]

DENIED_KEYWORDS = [
    "guaranteed cure", "miracle cure", "natural cure for cancer",
    "alternative medicine cures", "essential oils cure cancer",
    "skip chemo", "don't trust doctors", "big pharma conspiracy",
    "cancer is fake", "cure cancer naturally guaranteed",
    "stop your medication", "stop treatment", "home remedy cures cancer",
    "doctors are lying", "chemotherapy is poison", "cancer is a hoax",
    "secret cure", "they don't want you to know",
    "herbal cure cancer", "holistic cure cancer", "cannabis cures cancer",
    "cure without chemo", "refuse treatment", "doctors kill patients",
    "modern medicine is poison", "pharma kills",
]

MILD_WARNING_KEYWORDS = [
    "alternative treatment", "natural remedy", "supplement helped",
    "detox cured", "diet cured my",
]


def _check_safety(text: str) -> bool:
    lower = text.lower()
    return any(kw in lower for kw in DENIED_KEYWORDS)


def _check_mild_warning(text: str) -> bool:
    lower = text.lower()
    return any(kw in lower for kw in MILD_WARNING_KEYWORDS)


def _build_post_response(post: models.Post, current_user_id: Optional[int] = None) -> dict:
    reaction_counts = {}
    for r in post.reactions:
        reaction_counts[r.reaction_type] = reaction_counts.get(r.reaction_type, 0) + 1

    user_reaction = None
    if current_user_id:
        for r in post.reactions:
            if r.user_id == current_user_id:
                user_reaction = r.reaction_type
                break

    content = post.content
    if _check_mild_warning(content) and not post.is_flagged:
        content = (
            content
            + "\n\n\u2139\ufe0f Note: This post mentions approaches that may not be scientifically verified. "
            + "Always consult your medical team before changing your treatment plan."
        )

    return {
        "id": post.id,
        "title": post.title,
        "content": content,
        "category": post.category,
        "image_url": post.image_url,
        "is_flagged": post.is_flagged,
        "pinned": post.pinned,
        "created_at": post.created_at,
        "user_id": None if post.is_anonymous else post.user_id,
        "author_name": "Community Member" if post.is_anonymous else (post.author.full_name if post.author else None),
        "comment_count": len(post.comments),
        "reaction_counts": reaction_counts,
        "user_reaction": user_reaction,
        "group_id": post.group_id,
        "is_anonymous": post.is_anonymous,
        "comments": [],
    }


@router.get("/guidelines")
def get_guidelines() -> Any:
    return {
        "guidelines": [
            "Be kind and supportive — everyone here is on a personal journey.",
            "Share your experiences, but never offer medical diagnoses.",
            "Report harmful content using the flag option on any post.",
            "This is an educational space — always consult your doctor for medical decisions.",
            "Respect privacy. Do not share others' personal health information.",
            "Misinformation about cancer treatments will be removed immediately.",
            "No harassment, hate speech, or discrimination of any kind.",
            "Do not impersonate medical professionals.",
            "Sensitive images must be marked appropriately.",
        ],
        "disclaimer": "OncoAI Community is an educational support platform only. Always consult your medical team for health decisions.",
    }


@router.get("/posts")
def read_posts(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    sort: Optional[str] = "recent",
    group_id: Optional[int] = None,
) -> Any:
    query = db.query(models.Post).filter(models.Post.is_hidden == False)

    if category and category in VALID_CATEGORIES:
        query = query.filter(models.Post.category == category)
    if group_id:
        query = query.filter(models.Post.group_id == group_id)

    if sort == "supported":
        posts = query.order_by(models.Post.pinned.desc()).all()
        posts.sort(key=lambda p: len(p.reactions), reverse=True)
        posts = posts[skip : skip + limit]
    else:
        posts = (
            query.order_by(models.Post.pinned.desc(), models.Post.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    return [_build_post_response(p) for p in posts]


@router.get("/posts/{post_id}")
def read_post(post_id: int, db: Session = Depends(get_db)) -> Any:
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post or post.is_hidden:
        raise HTTPException(status_code=404, detail="Post not found")

    result = _build_post_response(post)
    comments = []
    for c in post.comments:
        comment_content = c.content
        if c.is_flagged:
            comment_content = "[This comment has been flagged for review] " + comment_content
        if _check_mild_warning(c.content) and not c.is_flagged:
            comment_content = comment_content + "\n\n\u2139\ufe0f This comment mentions approaches that may not be scientifically verified."
        comments.append({
            "id": c.id, "content": comment_content, "created_at": c.created_at,
            "user_id": c.user_id, "author_name": c.author.full_name if c.author else None,
            "is_flagged": c.is_flagged,
        })
    result["comments"] = comments
    return result


@router.post("/posts")
def create_post(
    *,
    db: Session = Depends(get_db),
    post_in: schemas.post.PostCreate,
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    if current_user.strike_count >= 2:
        raise HTTPException(status_code=403, detail="Your account is temporarily restricted.")

    if post_in.category not in VALID_CATEGORIES:
        raise HTTPException(status_code=400, detail="Invalid category")

    if post_in.group_id:
        group = db.query(models.Group).filter(models.Group.id == post_in.group_id).first()
        if not group:
            raise HTTPException(status_code=400, detail="Group not found")

    is_flagged = _check_safety(post_in.title) or _check_safety(post_in.content)

    post = models.Post(
        title=post_in.title, content=post_in.content, category=post_in.category,
        image_url=post_in.image_url, is_flagged=is_flagged,
        flag_reason="Auto-flagged: potential misinformation keywords" if is_flagged else None,
        user_id=current_user.id, group_id=post_in.group_id,
        is_anonymous=post_in.is_anonymous,
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    post = db.query(models.Post).filter(models.Post.id == post.id).first()
    return _build_post_response(post, current_user.id)


@router.delete("/posts/{post_id}")
def delete_post(post_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(deps.get_current_user)) -> Any:
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")
    db.delete(post)
    db.commit()
    return {"detail": "Post deleted"}


@router.post("/posts/{post_id}/react")
def react_to_post(
    post_id: int, reaction_in: schemas.reaction.ReactionCreate,
    db: Session = Depends(get_db), current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    if reaction_in.reaction_type not in VALID_REACTIONS:
        raise HTTPException(status_code=400, detail="Invalid reaction type")

    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post or post.is_hidden:
        raise HTTPException(status_code=404, detail="Post not found")

    existing = db.query(models.PostReaction).filter(
        models.PostReaction.post_id == post_id,
        models.PostReaction.user_id == current_user.id,
        models.PostReaction.reaction_type == reaction_in.reaction_type,
    ).first()

    if existing:
        db.delete(existing)
        db.commit()
    else:
        reaction = models.PostReaction(post_id=post_id, user_id=current_user.id, reaction_type=reaction_in.reaction_type)
        db.add(reaction)
        db.commit()
        if post.user_id != current_user.id:
            create_notification(db, post.user_id, "reaction",
                f"{current_user.full_name} sent you {reaction_in.reaction_type} on your post", "post", post.id)
            db.commit()

    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    return _build_post_response(post, current_user.id)


@router.delete("/posts/{post_id}/react/{reaction_type}")
def remove_reaction(post_id: int, reaction_type: str, db: Session = Depends(get_db), current_user: models.User = Depends(deps.get_current_user)) -> Any:
    reaction = db.query(models.PostReaction).filter(
        models.PostReaction.post_id == post_id,
        models.PostReaction.user_id == current_user.id,
        models.PostReaction.reaction_type == reaction_type,
    ).first()
    if not reaction:
        raise HTTPException(status_code=404, detail="Reaction not found")
    db.delete(reaction)
    db.commit()
    return {"detail": "Reaction removed"}


@router.get("/posts/{post_id}/comments")
def read_comments(post_id: int, db: Session = Depends(get_db)) -> Any:
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post or post.is_hidden:
        raise HTTPException(status_code=404, detail="Post not found")
    return [{
        "id": c.id, "content": c.content, "created_at": c.created_at,
        "user_id": c.user_id, "post_id": c.post_id,
        "author_name": c.author.full_name if c.author else None, "is_flagged": c.is_flagged,
    } for c in post.comments]


@router.post("/posts/{post_id}/comments")
def create_comment(
    post_id: int, comment_in: schemas.post.CommentContent,
    db: Session = Depends(get_db), current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    if current_user.strike_count >= 2:
        raise HTTPException(status_code=403, detail="Your account is temporarily restricted.")

    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post or post.is_hidden:
        raise HTTPException(status_code=404, detail="Post not found")

    is_flagged = _check_safety(comment_in.content)
    comment = models.Comment(content=comment_in.content, post_id=post_id, user_id=current_user.id, is_flagged=is_flagged)
    db.add(comment)
    db.commit()
    db.refresh(comment)

    if post.user_id != current_user.id:
        create_notification(db, post.user_id, "comment",
            f"{current_user.full_name} commented on your post", "post", post.id)
        db.commit()

    return {
        "id": comment.id, "content": comment.content, "created_at": comment.created_at,
        "user_id": comment.user_id, "post_id": comment.post_id,
        "author_name": current_user.full_name, "is_flagged": comment.is_flagged,
    }


@router.delete("/comments/{comment_id}")
def delete_comment(comment_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(deps.get_current_user)) -> Any:
    comment = db.query(models.Comment).filter(models.Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if comment.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")
    db.delete(comment)
    db.commit()
    return {"detail": "Comment deleted"}


@router.post("/posts/{post_id}/flag")
def flag_post(post_id: int, flag_in: schemas.post.FlagCreate, db: Session = Depends(get_db), current_user: models.User = Depends(deps.get_current_user)) -> Any:
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    post.is_flagged = True
    post.flag_reason = flag_in.reason
    post.flagged_by = current_user.id
    db.commit()
    return {"detail": "Post flagged for moderation"}
