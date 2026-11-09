from __future__ import annotations

from datetime import UTC, datetime

from fastapi import HTTPException, Response, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.api.deps import DB, CurrentUser, Paging
from app.api.router import SlashRouter
from app.models import Comment, Post, Reaction, Report, User
from app.models.enums import ContentStatus, PostTopic, ReactionKind, ReportStatus, Role
from app.schemas.common import Page
from app.schemas.community import (
    Author,
    CommentCreate,
    CommentOut,
    PostCreate,
    PostDetail,
    PostOut,
    ReactionCounts,
    ReactionIn,
    ReactionsOut,
    ReportCreated,
    ReportIn,
)
from app.services.moderation import (
    ANONYMOUS_NAME,
    AUTO_HIDE_REPORTS,
    PRIVACY_MESSAGE,
    contains_contact_details,
    display_name,
    mask_profanity,
)

router = SlashRouter(prefix="/community", tags=["community"])

MODERATOR_ROLES = {Role.moderator.value, Role.admin.value}


def is_moderator(user: User) -> bool:
    return user.role in MODERATOR_ROLES


def _clean(*texts: str) -> list[str]:
    if any(contains_contact_details(t) for t in texts):
        raise HTTPException(422, PRIVACY_MESSAGE)
    return [mask_profanity(t.strip()) for t in texts]


def _author(db: Session, user_id: int, anonymous: bool, names: dict[int, str] | None = None) -> Author:
    if anonymous:
        return Author(id=None, display_name=ANONYMOUS_NAME)
    if names is not None and user_id in names:
        return Author(id=user_id, display_name=names[user_id])
    user = db.get(User, user_id)
    return Author(id=user_id, display_name=display_name(user.full_name) if user else "Member")


def _reaction_state(db: Session, post_ids: list[int], viewer_id: int) -> tuple[dict[int, ReactionCounts], dict[int, list[str]]]:
    counts: dict[int, ReactionCounts] = {pid: ReactionCounts() for pid in post_ids}
    mine: dict[int, list[str]] = {pid: [] for pid in post_ids}
    if not post_ids:
        return counts, mine
    for post_id, kind, n in db.execute(
        select(Reaction.post_id, Reaction.kind, func.count(Reaction.id))
        .where(Reaction.post_id.in_(post_ids))
        .group_by(Reaction.post_id, Reaction.kind)
    ).all():
        setattr(counts[post_id], kind, n)
    for post_id, kind in db.execute(
        select(Reaction.post_id, Reaction.kind).where(Reaction.post_id.in_(post_ids), Reaction.user_id == viewer_id)
    ).all():
        mine[post_id].append(kind)
    for kinds in mine.values():
        kinds.sort(key=[k.value for k in ReactionKind].index)
    return counts, mine


def _posts_out(db: Session, posts: list[Post], viewer: User) -> list[PostOut]:
    ids = [p.id for p in posts]
    counts, mine = _reaction_state(db, ids, viewer.id)
    comment_counts: dict[int, int] = {}
    if ids:
        comment_counts = dict(
            db.execute(
                select(Comment.post_id, func.count(Comment.id))
                .where(Comment.post_id.in_(ids), Comment.status == ContentStatus.visible.value)
                .group_by(Comment.post_id)
            ).all()
        )
    author_ids = {p.user_id for p in posts if not p.anonymous}
    names = {
        u.id: display_name(u.full_name)
        for u in db.scalars(select(User).where(User.id.in_(author_ids))).all()
    } if author_ids else {}
    return [
        PostOut(
            id=p.id,
            title=p.title,
            body=p.body,
            topic=p.topic,
            author=_author(db, p.user_id, p.anonymous, names),
            created_at=p.created_at,
            comment_count=comment_counts.get(p.id, 0),
            reactions=counts[p.id],
            my_reactions=mine[p.id],
            is_mine=p.user_id == viewer.id,
            status="removed" if p.status == ContentStatus.removed.value else "visible",
            under_review=p.status == ContentStatus.hidden.value,
        )
        for p in posts
    ]


def _comment_out(db: Session, c: Comment, viewer: User) -> CommentOut:
    return CommentOut(
        id=c.id,
        post_id=c.post_id,
        body=c.body,
        author=_author(db, c.user_id, c.anonymous),
        created_at=c.created_at,
        is_mine=c.user_id == viewer.id,
    )


def get_viewable_post(db: Session, post_id: int, viewer: User) -> Post:
    post = db.get(Post, post_id)
    if post is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found")
    if post.status == ContentStatus.visible.value or is_moderator(viewer):
        return post
    if post.status == ContentStatus.hidden.value and post.user_id == viewer.id:
        return post
    raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found")


def _interactive_post(db: Session, post_id: int, viewer: User) -> Post:
    post = get_viewable_post(db, post_id, viewer)
    if post.status != ContentStatus.visible.value:
        raise HTTPException(status.HTTP_409_CONFLICT, "This post is not open for interaction.")
    return post


@router.get("/posts", response_model=Page[PostOut])
def list_posts(user: CurrentUser, db: DB, paging: Paging, topic: PostTopic | None = None) -> Page[PostOut]:
    conditions = [
        or_(
            Post.status == ContentStatus.visible.value,
            (Post.status == ContentStatus.hidden.value) & (Post.user_id == user.id),
        )
    ]
    if topic is not None:
        conditions.append(Post.topic == topic.value)
    total = db.scalar(select(func.count(Post.id)).where(*conditions)) or 0
    posts = db.scalars(
        select(Post).where(*conditions).order_by(Post.created_at.desc(), Post.id.desc()).limit(paging.limit).offset(paging.offset)
    ).all()
    return Page(items=_posts_out(db, list(posts), user), total=total)


@router.post("/posts", response_model=PostOut, status_code=status.HTTP_201_CREATED)
def create_post(payload: PostCreate, user: CurrentUser, db: DB) -> PostOut:
    title, body = _clean(payload.title, payload.body)
    post = Post(user_id=user.id, title=title, body=body, topic=payload.topic.value, anonymous=payload.anonymous)
    db.add(post)
    db.commit()
    db.refresh(post)
    return _posts_out(db, [post], user)[0]


@router.get("/posts/{post_id}", response_model=PostDetail)
def read_post(post_id: int, user: CurrentUser, db: DB) -> PostDetail:
    post = get_viewable_post(db, post_id, user)
    comments = db.scalars(
        select(Comment)
        .where(Comment.post_id == post.id, Comment.status == ContentStatus.visible.value)
        .order_by(Comment.created_at.asc(), Comment.id.asc())
        .limit(500)
    ).all()
    out = _posts_out(db, [post], user)[0]
    return PostDetail(**out.model_dump(), comments=[_comment_out(db, c, user) for c in comments])


@router.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(post_id: int, user: CurrentUser, db: DB) -> Response:
    post = get_viewable_post(db, post_id, user)
    if post.user_id == user.id:
        db.delete(post)
    elif is_moderator(user):
        post.status = ContentStatus.removed.value
        _close_reports(db, user, post_id=post.id, outcome=ReportStatus.actioned)
    else:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You can only delete your own posts.")
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/posts/{post_id}/comments", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
def create_comment(post_id: int, payload: CommentCreate, user: CurrentUser, db: DB) -> CommentOut:
    post = _interactive_post(db, post_id, user)
    (body,) = _clean(payload.body)
    comment = Comment(post_id=post.id, user_id=user.id, body=body, anonymous=payload.anonymous)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return _comment_out(db, comment, user)


def _get_comment(db: Session, comment_id: int, viewer: User) -> Comment:
    comment = db.get(Comment, comment_id)
    if comment is None or (comment.status != ContentStatus.visible.value and not is_moderator(viewer)):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Comment not found")
    get_viewable_post(db, comment.post_id, viewer)
    return comment


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(comment_id: int, user: CurrentUser, db: DB) -> Response:
    comment = _get_comment(db, comment_id, user)
    if comment.user_id == user.id:
        db.delete(comment)
    elif is_moderator(user):
        comment.status = ContentStatus.removed.value
        _close_reports(db, user, comment_id=comment.id, outcome=ReportStatus.actioned)
    else:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You can only delete your own comments.")
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/posts/{post_id}/reactions", response_model=ReactionsOut)
def toggle_reaction(post_id: int, payload: ReactionIn, user: CurrentUser, db: DB) -> ReactionsOut:
    post = _interactive_post(db, post_id, user)
    existing = db.scalar(
        select(Reaction).where(Reaction.post_id == post.id, Reaction.user_id == user.id, Reaction.kind == payload.kind.value)
    )
    if existing is not None:
        db.delete(existing)
    else:
        db.add(Reaction(post_id=post.id, user_id=user.id, kind=payload.kind.value))
    db.commit()
    counts, mine = _reaction_state(db, [post.id], user.id)
    return ReactionsOut(reactions=counts[post.id], my_reactions=mine[post.id])


def _open_report_count(db: Session, *, post_id: int | None = None, comment_id: int | None = None) -> int:
    target = Report.post_id == post_id if post_id is not None else Report.comment_id == comment_id
    return db.scalar(select(func.count(Report.id)).where(target, Report.status == ReportStatus.open.value)) or 0


def _close_reports(
    db: Session, moderator: User, *, outcome: ReportStatus, post_id: int | None = None, comment_id: int | None = None
) -> None:
    target = Report.post_id == post_id if post_id is not None else Report.comment_id == comment_id
    for report in db.scalars(select(Report).where(target, Report.status == ReportStatus.open.value)):
        report.status = outcome.value
        report.resolved_by_id = moderator.id
        report.resolved_at = datetime.now(UTC)


def _file_report(db: Session, reporter: User, reason: str, *, post: Post | None = None, comment: Comment | None = None) -> ReportCreated:
    target = Report.post_id == post.id if post is not None else Report.comment_id == comment.id  # type: ignore[union-attr]
    existing = db.scalar(
        select(Report).where(target, Report.reporter_id == reporter.id, Report.status == ReportStatus.open.value)
    )
    if existing is not None:
        return ReportCreated(id=existing.id)
    report = Report(
        reporter_id=reporter.id,
        post_id=post.id if post is not None else None,
        comment_id=comment.id if comment is not None else None,
        reason=reason.strip(),
    )
    db.add(report)
    db.flush()
    content = post if post is not None else comment
    assert content is not None
    open_count = _open_report_count(
        db, post_id=post.id if post is not None else None, comment_id=comment.id if comment is not None else None
    )
    if open_count >= AUTO_HIDE_REPORTS and content.status == ContentStatus.visible.value:
        content.status = ContentStatus.hidden.value
    db.commit()
    return ReportCreated(id=report.id)


@router.post("/posts/{post_id}/report", response_model=ReportCreated, status_code=status.HTTP_201_CREATED)
def report_post(post_id: int, payload: ReportIn, user: CurrentUser, db: DB) -> ReportCreated:
    post = get_viewable_post(db, post_id, user)
    if post.user_id == user.id:
        raise HTTPException(422, "You can't report your own post.")
    return _file_report(db, user, payload.reason, post=post)


@router.post("/comments/{comment_id}/report", response_model=ReportCreated, status_code=status.HTTP_201_CREATED)
def report_comment(comment_id: int, payload: ReportIn, user: CurrentUser, db: DB) -> ReportCreated:
    comment = _get_comment(db, comment_id, user)
    if comment.user_id == user.id:
        raise HTTPException(422, "You can't report your own comment.")
    return _file_report(db, user, payload.reason, comment=comment)
