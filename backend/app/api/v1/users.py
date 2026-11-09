from __future__ import annotations

from fastapi import HTTPException, Response, status

from app.api.deps import DB, CurrentUser
from app.api.router import SlashRouter
from app.core.security import hash_password, verify_password
from app.models import User
from app.schemas.user import PasswordChangeIn, UserOut, UserUpdate
from app.services import storage

router = SlashRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
def read_me(user: CurrentUser) -> User:
    return user


@router.patch("/me", response_model=UserOut)
def update_me(payload: UserUpdate, user: CurrentUser, db: DB) -> User:
    for field, value in payload.model_dump(exclude_unset=True).items():
        if field == "full_name" and value is None:
            continue
        setattr(user, field, value.strip() if isinstance(value, str) else value)
    db.commit()
    db.refresh(user)
    return user


@router.post("/me/password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(payload: PasswordChangeIn, user: CurrentUser, db: DB) -> Response:
    if not verify_password(payload.current_password, user.hashed_password):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Current password is incorrect.")
    user.hashed_password = hash_password(payload.new_password)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_me(user: CurrentUser, db: DB) -> Response:
    user_id = user.id
    db.delete(user)
    db.commit()
    storage.delete_user_files(user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
