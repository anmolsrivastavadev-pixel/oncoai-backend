"""Shared FastAPI dependencies: DB session, authentication, roles, pagination, limits."""

from __future__ import annotations

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, Query, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core import rate_limit
from app.core.config import settings
from app.core.security import TokenError, decode_token
from app.db.session import get_db
from app.models import User
from app.models.enums import Role

bearer_scheme = HTTPBearer(auto_error=False)

DB = Annotated[Session, Depends(get_db)]


def _unauthorized(detail: str = "Not authenticated") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    db: DB,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthorized()
    try:
        user_id = decode_token(credentials.credentials, "access")
    except TokenError as exc:
        raise _unauthorized("Invalid or expired token") from exc
    user = db.get(User, user_id)
    if user is None:
        raise _unauthorized("Invalid or expired token")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_role(*roles: Role) -> Callable[[User], User]:
    allowed = {r.value for r in roles}

    def dependency(user: CurrentUser) -> User:
        if user.role not in allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return user

    return dependency


class Pagination:
    def __init__(
        self,
        limit: Annotated[int, Query(ge=1, le=100)] = 20,
        offset: Annotated[int, Query(ge=0, le=1_000_000)] = 0,
    ) -> None:
        self.limit = limit
        self.offset = offset


Paging = Annotated[Pagination, Depends()]


def auth_rate_limit(request: Request) -> None:
    rate_limit.enforce(
        f"auth:ip:{rate_limit.client_ip(request)}", settings.RATE_LIMIT_AUTH_PER_MINUTE
    )


def user_rate_limit(scope: str, limit_getter: Callable[[], int]) -> Callable[[User], None]:
    def dependency(user: CurrentUser) -> None:
        rate_limit.enforce(f"{scope}:user:{user.id}", limit_getter())

    return dependency


scan_rate_limit = user_rate_limit("scans", lambda: settings.RATE_LIMIT_SCANS_PER_MINUTE)
assistant_rate_limit = user_rate_limit(
    "assistant", lambda: settings.RATE_LIMIT_ASSISTANT_PER_MINUTE
)
