from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated, Literal

from fastapi import Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import DB, Paging, require_role
from app.api.router import SlashRouter
from app.models import Comment, Post, Report, User
from app.models.enums import ContentStatus, ReportStatus, Role
from app.schemas.common import Page
from app.schemas.community import ReportOut, ResolveIn

router = SlashRouter(prefix="/moderation", tags=["moderation"])

Moderator = Annotated[User, Depends(require_role(Role.moderator, Role.admin))]


def _target(db: Session, report: Report) -> Post | Comment | None:
    if report.post_id is not None:
        return db.get(Post, report.post_id)
    return db.get(Comment, report.comment_id) if report.comment_id is not None else None


def _report_out(db: Session, report: Report) -> ReportOut:
    target = _target(db, report)
    if isinstance(target, Post):
        preview = f"{target.title}: {target.body}"
        post_id = target.id
        same_target = Report.post_id == report.post_id
    else:
        preview = target.body if target else ""
        post_id = target.post_id if target else 0
        same_target = Report.comment_id == report.comment_id
    open_count = db.scalar(
        select(func.count(Report.id)).where(same_target, Report.status == ReportStatus.open.value)
    ) or 0
    return ReportOut(
        id=report.id,
        target_type="post" if report.post_id is not None else "comment",
        post_id=post_id,
        comment_id=report.comment_id,
        reason=report.reason,
        status=report.status,  # type: ignore[arg-type]
        created_at=report.created_at,
        content_preview=preview[:300],
        open_report_count=open_count,
        reporter_id=report.reporter_id,
    )


@router.get("/reports", response_model=Page[ReportOut])
def list_reports(
    _: Moderator,
    db: DB,
    paging: Paging,
    status_filter: Annotated[
        Literal["open", "dismissed", "actioned", "all"], Query(alias="status")
    ] = "open",
) -> Page[ReportOut]:
    conditions = [] if status_filter == "all" else [Report.status == status_filter]
    total = db.scalar(select(func.count(Report.id)).where(*conditions)) or 0
    reports = db.scalars(
        select(Report).where(*conditions).order_by(Report.created_at.asc(), Report.id.asc()).limit(paging.limit).offset(paging.offset)
    ).all()
    return Page(items=[_report_out(db, r) for r in reports], total=total)


@router.post("/reports/{report_id}/resolve", response_model=ReportOut)
def resolve_report(report_id: int, payload: ResolveIn, moderator: Moderator, db: DB) -> ReportOut:
    report = db.get(Report, report_id)
    if report is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Report not found")
    target = _target(db, report)
    if report.post_id is not None:
        same_target = Report.post_id == report.post_id
    else:
        same_target = Report.comment_id == report.comment_id

    if payload.action == "remove_content":
        outcome = ReportStatus.actioned
        if target is not None:
            target.status = ContentStatus.removed.value
    else:
        outcome = ReportStatus.dismissed
        if target is not None and target.status == ContentStatus.hidden.value:
            target.status = ContentStatus.visible.value

    now = datetime.now(UTC)
    # Resolving one report settles every open report on the same content.
    for item in db.scalars(select(Report).where(same_target, Report.status == ReportStatus.open.value)):
        item.status = outcome.value
        item.resolved_by_id = moderator.id
        item.resolved_at = now
    if report.status == ReportStatus.open.value:
        report.status = outcome.value
        report.resolved_by_id = moderator.id
        report.resolved_at = now
    db.commit()
    db.refresh(report)
    return _report_out(db, report)
