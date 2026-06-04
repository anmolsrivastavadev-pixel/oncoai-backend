from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import schemas, models
from app.core import security
from app.core.config import settings
from app.db.session import get_db
from app.api import deps

router = APIRouter()

@router.post("/signup", response_model=schemas.user.User)
def create_user(*, db: Session = Depends(get_db), user_in: schemas.user.UserCreate) -> Any:
    user = db.query(models.User).filter(models.User.email == user_in.email).first()
    if user:
        raise HTTPException(status_code=400, detail="The user with this email already exists in the system.")
    if len(user_in.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters long.")
    db_obj = models.User(email=user_in.email, hashed_password=security.get_password_hash(user_in.password), full_name=user_in.full_name)
    db.add(db_obj); db.commit(); db.refresh(db_obj)
    return db_obj

@router.post("/login")
def login_access_token(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()) -> Any:
    email = form_data.username.strip()
    password = form_data.password
    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password are required")
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user or not security.verify_password(password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {"access_token": security.create_access_token(user.id, expires_delta=access_token_expires), "token_type": "bearer"}

@router.get("/me", response_model=schemas.user.User)
def read_user_me(current_user: models.User = Depends(deps.get_current_user)) -> Any:
    return current_user
