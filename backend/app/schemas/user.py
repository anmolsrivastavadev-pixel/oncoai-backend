from __future__ import annotations

import re
from datetime import date
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.common import ORMModel, UTCDateTime

SkinType = Literal["I", "II", "III", "IV", "V", "VI"]


def validate_password_strength(value: str) -> str:
    if len(value) < 8:
        raise ValueError("Password must be at least 8 characters long.")
    if len(value.encode("utf-8")) > 72:
        raise ValueError("Password must be at most 72 bytes long.")
    if not re.search(r"[A-Za-z]", value) or not re.search(r"\d", value):
        raise ValueError("Password must contain at least one letter and one digit.")
    return value


class UserOut(ORMModel):
    id: int
    email: str
    full_name: str
    date_of_birth: date | None
    skin_type: SkinType | None
    location: str | None
    bio: str | None
    role: Literal["user", "moderator", "admin"]
    created_at: UTCDateTime


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(max_length=128)
    full_name: str = Field(min_length=1, max_length=120)

    @field_validator("password")
    @classmethod
    def _strong(cls, value: str) -> str:
        return validate_password_strength(value)

    @field_validator("full_name")
    @classmethod
    def _strip(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Full name is required.")
        return value


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(max_length=128)


class RefreshIn(BaseModel):
    refresh_token: str = Field(max_length=4096)


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"
    user: UserOut


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=120)
    date_of_birth: date | None = None
    skin_type: SkinType | None = None
    location: str | None = Field(default=None, max_length=120)
    bio: str | None = Field(default=None, max_length=2000)

    @field_validator("date_of_birth")
    @classmethod
    def _not_future(cls, value: date | None) -> date | None:
        if value is not None and value > date.today():
            raise ValueError("Date of birth cannot be in the future.")
        return value


class PasswordChangeIn(BaseModel):
    current_password: str = Field(max_length=128)
    new_password: str = Field(max_length=128)

    @field_validator("new_password")
    @classmethod
    def _strong(cls, value: str) -> str:
        return validate_password_strength(value)
