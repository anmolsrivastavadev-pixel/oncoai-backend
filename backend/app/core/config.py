"""Application settings loaded from environment variables (and an optional .env file)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]

DEFAULT_SECRET_KEY = "dev-insecure-secret-key-change-me-0123456789"

DISCLAIMER = (
    "OncoAI is an educational skin health awareness platform and does not provide "
    "medical diagnosis or treatment advice."
)

# Default label -> weight map for the HAM10000 ViT checkpoint
# (Anwarkh1/Skin_Cancer-Image_Classification). Matched case-insensitively.
DEFAULT_LABEL_WEIGHTS: dict[str, float] = {
    "melanoma": 1.0,
    "basal_cell_carcinoma": 1.0,
    "actinic_keratoses": 0.6,
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env", env_file_encoding="utf-8", extra="ignore"
    )

    ENVIRONMENT: Literal["development", "test", "production"] = "development"
    PROJECT_NAME: str = "OncoAI API"
    API_V1_PREFIX: str = "/api/v1"
    LOG_LEVEL: str = "INFO"
    LOG_JSON: bool = True

    DATABASE_URL: str = "postgresql+psycopg://oncoai:oncoai@localhost:5432/oncoai"

    SECRET_KEY: str = DEFAULT_SECRET_KEY
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 14
    BCRYPT_ROUNDS: int = Field(default=12, ge=4, le=16)

    CORS_ORIGINS: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "capacitor://localhost",
            "http://localhost",
            "https://localhost",
        ]
    )

    UPLOAD_DIR: Path = BACKEND_DIR / "uploads"
    MAX_UPLOAD_BYTES: int = 10 * 1024 * 1024
    MAX_IMAGE_PIXELS: int = 40_000_000
    IMAGE_ENCRYPTION_KEY: str | None = None

    MODEL_DIR: Path = BACKEND_DIR / "models" / "skin-lesion-vit"
    MODEL_REPO_ID: str = "Anwarkh1/Skin_Cancer-Image_Classification"
    # User-facing model name (kept neutral: no disease names in API responses).
    MODEL_DISPLAY_NAME: str = "OncoAI visual pattern model (ViT)"
    MODEL_LABEL_WEIGHTS: dict[str, float] = Field(
        default_factory=lambda: dict(DEFAULT_LABEL_WEIGHTS)
    )
    MODEL_WARMUP: bool = True
    ANALYZER_KIND: Literal["auto", "vit", "heuristic"] = "auto"

    ANTHROPIC_API_KEY: str | None = None
    ASSISTANT_MODEL: str = "claude-opus-5-5"
    ASSISTANT_MAX_TOKENS: int = 2048
    ASSISTANT_TIMEOUT_SECONDS: float = 60.0

    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_AUTH_PER_MINUTE: int = 5
    RATE_LIMIT_SCANS_PER_MINUTE: int = 20
    RATE_LIMIT_ASSISTANT_PER_MINUTE: int = 20

    SEED_SAMPLE_DATA: bool = True

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("ANTHROPIC_API_KEY", "IMAGE_ENCRYPTION_KEY", mode="before")
    @classmethod
    def _empty_to_none(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @model_validator(mode="after")
    def _check_production(self) -> Settings:
        if self.ENVIRONMENT == "production":
            if self.SECRET_KEY == DEFAULT_SECRET_KEY or len(self.SECRET_KEY) < 32:
                raise ValueError(
                    "SECRET_KEY must be set to a random value of at least 32 characters "
                    "when ENVIRONMENT=production"
                )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
