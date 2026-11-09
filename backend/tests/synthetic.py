"""Synthetic test images: a regular uniform dark disc vs. an irregular multi-coloured blob."""

from __future__ import annotations

import io

import cv2
import numpy as np
from PIL import Image

SKIN = (224, 182, 150)


def _skin_background(size: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    base = np.full((size, size, 3), SKIN, dtype=np.float32)
    # Gentle skin-like texture so blur/contrast metrics resemble a real photo.
    noise = rng.normal(0, 6, (size, size, 1)).astype(np.float32)
    texture = cv2.GaussianBlur(rng.normal(0, 10, (size, size)).astype(np.float32), (0, 0), 3)
    base += noise + texture[..., None]
    return base


def regular_spot(size: int = 512, seed: int = 1) -> np.ndarray:
    img = _skin_background(size, seed)
    cv2.circle(img, (size // 2, size // 2), size // 7, (95, 62, 45), thickness=-1, lineType=cv2.LINE_AA)
    rng = np.random.default_rng(seed + 100)
    img += rng.normal(0, 3, img.shape).astype(np.float32)
    return np.clip(img, 0, 255).astype(np.uint8)


def irregular_spot(size: int = 512, seed: int = 2) -> np.ndarray:
    img = _skin_background(size, seed)
    rng = np.random.default_rng(seed)
    centre = np.array([size / 2, size / 2])
    angles = np.linspace(0, 2 * np.pi, 48, endpoint=False)
    radii = size * (0.11 + 0.10 * rng.random(48))
    radii[:16] *= 1.6  # one lobe much larger -> asymmetric
    pts = np.stack([centre[0] + radii * np.cos(angles), centre[1] + radii * np.sin(angles)], 1)
    mask = np.zeros((size, size), np.uint8)
    cv2.fillPoly(mask, [pts.astype(np.int32)], 255)
    colours = [(60, 35, 30), (120, 70, 50), (30, 25, 45), (150, 60, 70)]
    region = np.zeros((size, size), np.int32)
    for i in range(1, 4):
        cx, cy = centre + rng.normal(0, size * 0.07, 2)
        cv2.circle(region, (int(cx), int(cy)), int(size * (0.05 + 0.03 * i)), i, -1)
    for i, colour in enumerate(colours):
        sel = (mask > 0) & (region == i)
        img[sel] = colour
    img += rng.normal(0, 3, img.shape).astype(np.float32)
    return np.clip(img, 0, 255).astype(np.uint8)


def to_jpeg(image: np.ndarray, *, exif: bytes | None = None, quality: int = 92) -> bytes:
    buf = io.BytesIO()
    pil = Image.fromarray(image)
    kwargs = {"quality": quality}
    if exif is not None:
        kwargs["exif"] = exif
    pil.save(buf, format="JPEG", **kwargs)
    return buf.getvalue()
