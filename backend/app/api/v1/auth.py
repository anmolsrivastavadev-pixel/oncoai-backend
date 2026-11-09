from __future__ import annotations

from fastapi import Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.api.deps import DB, auth_rate_limit
from app.api.router import SlashRouter
from app.core.security import (
    DUMMY_PASSWORD_HASH,
    TokenError,
    create_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models import User
from app.schemas.user import LoginIn, RefreshIn, RegisterIn, TokenPair, UserOut

router = SlashRouter(prefix="/auth", tags=["auth"])


def token_pair(user: User) -> TokenPair:
    return TokenPair(
        access_token=create_token(user.id, "access"),
        refresh_token=create_token(user.id, "refresh"),
        user=UserOut.model_validate(user),
    )


@router.post(
    "/register",
    response_model=TokenPair,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(auth_rate_limit)],
)
def register(payload: RegisterIn, db: DB) -> TokenPair:
    email = payload.email.lower()
    if db.scalar(select(User.id).where(func.lower(User.email) == email)) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "An account with this email already exists.")
    user = User(email=email, hashed_password=hash_password(payload.password), full_name=payload.full_name)
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "An account with this email already exists.") from exc
    db.refresh(user)
    return token_pair(user)


@router.post("/login", response_model=TokenPair, dependencies=[Depends(auth_rate_limit)])
def login(payload: LoginIn, db: DB) -> TokenPair:
    user = db.scalar(select(User).where(func.lower(User.email) == payload.email.lower()))
    if user is None:
        verify_password(payload.password, DUMMY_PASSWORD_HASH)  # equalise timing
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Incorrect email or password.", {"WWW-Authenticate": "Bearer"}
        )
    if not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Incorrect email or password.", {"WWW-Authenticate": "Bearer"}
        )
    return token_pair(user)


@router.post("/refresh", response_model=TokenPair)
def refresh(payload: RefreshIn, db: DB) -> TokenPair:
    try:
        user_id = decode_token(payload.refresh_token, "refresh")
    except TokenError as exc:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Invalid or expired refresh token.", {"WWW-Authenticate": "Bearer"}
        ) from exc
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Invalid or expired refresh token.", {"WWW-Authenticate": "Bearer"}
        )
    return token_pair(user)
