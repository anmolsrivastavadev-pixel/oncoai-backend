from __future__ import annotations

from fastapi import Depends

from app.api.deps import DB, CurrentUser, assistant_rate_limit
from app.api.router import SlashRouter
from app.schemas.assistant import ChatIn, ChatOut, TopicOut
from app.schemas.common import Items
from app.services.assistant import service
from app.services.scan_service import get_owned_scan

router = SlashRouter(prefix="/assistant", tags=["assistant"])


@router.post("/chat", response_model=ChatOut, dependencies=[Depends(assistant_rate_limit)])
def chat(payload: ChatIn, user: CurrentUser, db: DB) -> ChatOut:
    scan = None
    if payload.context and payload.context.scan_id is not None:
        scan = get_owned_scan(db, user.id, payload.context.scan_id)
    return service.chat(db, payload, scan)


@router.get("/topics", response_model=Items[TopicOut])
def topics() -> Items[TopicOut]:
    return Items(items=service.list_topics())
