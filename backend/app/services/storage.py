"""Protected image handling.

* Uploads are fully decoded with Pillow (rejecting anything that is not a real image).
* EXIF orientation is applied, then ALL metadata (EXIF incl. GPS, ICC, XMP, comments) is
  dropped by re-encoding pixel data only into a fresh JPEG (quality 90).
* Files live under ``settings.UPLOAD_DIR/<user_id>/`` which is never mounted as static
  content; they are served only through the owner-checked scan image endpoint.
* Optional at-rest encryption with Fernet when ``IMAGE_ENCRYPTION_KEY`` is set.
"""

from __future__ import annotations

import io
import logging
import os
import shutil
import uuid
import warnings
from dataclasses import dataclass
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken
from PIL import Image, ImageOps, UnidentifiedImageError

from app.core.config import settings

logger = logging.getLogger(__name__)

ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}
THUMB_EDGE = 256
JPEG_QUALITY = 90
ENCRYPTED_SUFFIX = ".enc"


class ImageValidationError(ValueError):
    def __init__(self, message: str, status_code: int = 422) -> None:
        super().__init__(message)
        self.status_code = status_code


@dataclass(frozen=True)
class ProcessedImage:
    image: Image.Image  # RGB, orientation-corrected, metadata-free
    jpeg: bytes
    thumbnail: bytes


@dataclass(frozen=True)
class StoredImage:
    image_path: str
    thumb_path: str


def _encode_jpeg(image: Image.Image) -> bytes:
    buf = io.BytesIO()
    image.save(buf, format="JPEG", quality=JPEG_QUALITY, optimize=True)
    return buf.getvalue()


def process_upload(raw: bytes) -> ProcessedImage:
    if not raw:
        raise ImageValidationError("The uploaded file is empty.")
    if len(raw) > settings.MAX_UPLOAD_BYTES:
        limit_mb = settings.MAX_UPLOAD_BYTES // (1024 * 1024)
        raise ImageValidationError(f"Image is larger than {limit_mb} MB.", status_code=413)

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            probe = Image.open(io.BytesIO(raw))
            if probe.format not in ALLOWED_FORMATS:
                raise ImageValidationError("Unsupported image type. Upload a JPEG, PNG or WebP photo.")
            width, height = probe.size
            if width * height > settings.MAX_IMAGE_PIXELS:
                raise ImageValidationError("Image resolution is too large (max 40 megapixels).")
            if width < 64 or height < 64:
                raise ImageValidationError("Image is too small. Use a photo at least 64x64 pixels.")
            probe.load()  # full decode: catches truncated / corrupt files
            oriented = ImageOps.exif_transpose(probe)
    except ImageValidationError:
        raise
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError, Image.DecompressionBombError,
            Image.DecompressionBombWarning) as exc:
        raise ImageValidationError("The file could not be read as an image.") from exc

    if oriented.mode in ("RGBA", "LA", "P"):
        rgba = oriented.convert("RGBA")
        background = Image.new("RGB", rgba.size, (255, 255, 255))
        background.paste(rgba, mask=rgba.getchannel("A"))
        rgb = background
    else:
        rgb = oriented.convert("RGB")
    # Rebuild from raw pixels so no metadata (info dict, ICC, EXIF, XMP) can survive.
    clean = Image.frombytes("RGB", rgb.size, rgb.tobytes())

    thumb = clean.copy()
    thumb.thumbnail((THUMB_EDGE, THUMB_EDGE), Image.Resampling.LANCZOS)
    return ProcessedImage(image=clean, jpeg=_encode_jpeg(clean), thumbnail=_encode_jpeg(thumb))


def _fernet() -> Fernet | None:
    key = settings.IMAGE_ENCRYPTION_KEY
    return Fernet(key.encode()) if key else None


def _root() -> Path:
    root = Path(settings.UPLOAD_DIR).resolve()
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    return root


def _safe_path(relative: str) -> Path:
    root = _root()
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        raise ValueError("Path escapes upload directory")
    return path


def _write_atomic(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    tmp = path.with_name(path.name + ".tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "wb") as handle:
        handle.write(data)
    os.replace(tmp, path)


def save_scan_images(user_id: int, processed: ProcessedImage) -> StoredImage:
    fernet = _fernet()
    suffix = ".jpg" + (ENCRYPTED_SUFFIX if fernet else "")
    stem = uuid.uuid4().hex
    image_rel = f"{user_id}/{stem}{suffix}"
    thumb_rel = f"{user_id}/{stem}_thumb{suffix}"
    for rel, data in ((image_rel, processed.jpeg), (thumb_rel, processed.thumbnail)):
        _write_atomic(_safe_path(rel), fernet.encrypt(data) if fernet else data)
    return StoredImage(image_path=image_rel, thumb_path=thumb_rel)


def read_image(relative: str) -> bytes:
    path = _safe_path(relative)
    data = path.read_bytes()
    if relative.endswith(ENCRYPTED_SUFFIX):
        fernet = _fernet()
        if fernet is None:
            raise RuntimeError("Image is encrypted but IMAGE_ENCRYPTION_KEY is not configured")
        try:
            return fernet.decrypt(data)
        except InvalidToken as exc:
            raise RuntimeError("Image could not be decrypted with the configured key") from exc
    return data


def delete_files(relatives: list[str]) -> None:
    for rel in relatives:
        try:
            _safe_path(rel).unlink(missing_ok=True)
        except (OSError, ValueError):
            logger.warning("could not delete stored image", extra={"path": rel})


def delete_user_files(user_id: int) -> None:
    path = _safe_path(str(int(user_id)))
    if path.is_dir():
        shutil.rmtree(path, ignore_errors=True)
