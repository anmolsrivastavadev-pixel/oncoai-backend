"""Classical computer-vision pipeline: image quality, lesion segmentation and
ABCDE-inspired visual features.

These are *visual pattern measurements* intended for educational awareness. They are not
a diagnosis and are not validated as a medical device. All scores are normalised to
0-100 where higher means "more irregular-looking".
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field

import cv2
import numpy as np
from numpy.typing import NDArray
from skimage import color as skcolor

logger = logging.getLogger(__name__)

ANALYSIS_EDGE = 512  # images are resized so the longest edge is this many pixels

# Quality thresholds (measured on the ANALYSIS_EDGE-normalised grayscale image).
BLUR_MIN = 40.0  # variance of Laplacian
BRIGHTNESS_MIN = 50.0
BRIGHTNESS_MAX = 225.0
CONTRAST_MIN = 18.0

MIN_AREA_FRACTION = 0.002
MAX_AREA_FRACTION = 0.85

RGBImage = NDArray[np.uint8]
Mask = NDArray[np.uint8]


@dataclass(frozen=True)
class QualityReport:
    ok: bool
    blur_score: float
    brightness: float
    contrast: float
    issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class LesionFeatures:
    asymmetry: float
    border_irregularity: float
    color_variation: float
    diameter_px: float
    diameter_relative: float
    color_count: int

    def to_dict(self) -> dict[str, float | int]:
        return asdict(self)


EMPTY_FEATURES = LesionFeatures(0.0, 0.0, 0.0, 0.0, 0.0, 0)


@dataclass(frozen=True)
class CVAnalysis:
    quality: QualityReport
    features: LesionFeatures
    segmented: bool
    cv_score: float | None  # None when no lesion could be isolated


def _clip100(value: float) -> float:
    return float(round(min(100.0, max(0.0, value)), 1))


def resize_for_analysis(image: RGBImage) -> tuple[RGBImage, float]:
    """Resize so the longest edge is ANALYSIS_EDGE. Returns (image, scale to original)."""
    h, w = image.shape[:2]
    longest = max(h, w)
    if longest == ANALYSIS_EDGE:
        return image, 1.0
    scale = ANALYSIS_EDGE / longest
    interp = cv2.INTER_AREA if scale < 1 else cv2.INTER_CUBIC
    resized = cv2.resize(image, (round(w * scale), round(h * scale)), interpolation=interp)
    return resized, 1.0 / scale


# ─── Quality ───────────────────────────────────────────────────────────────────


def assess_quality(image: RGBImage) -> QualityReport:
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    blur = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    brightness = float(gray.mean())
    contrast = float(gray.std())

    issues: list[str] = []
    if blur < BLUR_MIN:
        issues.append("The photo looks blurry. Hold the camera steady and tap the spot to focus.")
    if brightness < BRIGHTNESS_MIN:
        issues.append("The photo is too dark. Use daylight or a bright, even light source.")
    elif brightness > BRIGHTNESS_MAX:
        issues.append("The photo is overexposed. Avoid direct flash glare and harsh light.")
    if contrast < CONTRAST_MIN:
        issues.append("Low contrast. Make sure the spot is clearly visible against the skin.")

    return QualityReport(
        ok=not issues,
        blur_score=round(blur, 1),
        brightness=round(brightness, 1),
        contrast=round(contrast, 1),
        issues=issues,
    )


# ─── Segmentation ──────────────────────────────────────────────────────────────


def segment_lesion(image: RGBImage) -> Mask | None:
    """Return a binary mask (0/255) of the most plausible lesion, or None.

    Pigmented spots are darker than surrounding skin, so we threshold the CIE-LAB
    lightness channel after CLAHE contrast equalisation, using Otsu's method. Among the
    resulting regions we keep the largest one near the image centre (users are asked to
    centre the spot), ignoring regions that are tiny or fill nearly the whole frame.
    """
    h, w = image.shape[:2]
    lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
    lightness = lab[:, :, 0]
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(lightness)
    blurred = cv2.GaussianBlur(enhanced, (7, 7), 0)
    _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=2)

    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not contours:
        return None

    frame_area = float(h * w)
    centre = np.array([w / 2.0, h / 2.0])
    half_diag = float(np.hypot(w, h) / 2.0)
    best: tuple[float, NDArray[np.int32]] | None = None
    for contour in contours:
        area = cv2.contourArea(contour)
        fraction = area / frame_area
        if fraction < MIN_AREA_FRACTION or fraction > MAX_AREA_FRACTION:
            continue
        moments = cv2.moments(contour)
        if moments["m00"] == 0:
            continue
        centroid = np.array([moments["m10"] / moments["m00"], moments["m01"] / moments["m00"]])
        distance = float(np.linalg.norm(centroid - centre)) / half_diag
        # Prefer large, central regions; regions hugging the frame edge are penalised
        # because they are usually shadows, hair or vignetting.
        x, y, cw, ch = cv2.boundingRect(contour)
        touches_edge = x <= 1 or y <= 1 or x + cw >= w - 1 or y + ch >= h - 1
        score = area * (1.0 - 0.8 * distance) * (0.35 if touches_edge else 1.0)
        if best is None or score > best[0]:
            best = (score, contour)

    if best is None:
        return None
    mask = np.zeros((h, w), dtype=np.uint8)
    cv2.drawContours(mask, [best[1]], -1, 255, thickness=cv2.FILLED)
    return mask


def _largest_contour(mask: Mask) -> NDArray[np.int32]:
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    return max(contours, key=cv2.contourArea)


# ─── Features ──────────────────────────────────────────────────────────────────


def _align_mask(mask: Mask) -> Mask:
    """Rotate the mask so its principal axis is horizontal and centre it on its centroid."""
    moments = cv2.moments(mask, binaryImage=True)
    cx, cy = moments["m10"] / moments["m00"], moments["m01"] / moments["m00"]
    angle = 0.5 * np.degrees(np.arctan2(2 * moments["mu11"], moments["mu20"] - moments["mu02"]))
    h, w = mask.shape
    size = int(np.ceil(np.hypot(h, w)))
    matrix = cv2.getRotationMatrix2D((cx, cy), angle, 1.0)
    matrix[0, 2] += size / 2.0 - cx
    matrix[1, 2] += size / 2.0 - cy
    rotated = cv2.warpAffine(mask, matrix, (size, size), flags=cv2.INTER_NEAREST)
    return rotated


def asymmetry_score(mask: Mask) -> float:
    """Shape asymmetry about both principal axes (mask flip non-overlap)."""
    aligned = _align_mask(mask) > 0
    area = float(aligned.sum())
    if area == 0:
        return 0.0
    ratios = []
    for flipped in (np.flipud(aligned), np.fliplr(aligned)):
        ratios.append(float(np.logical_xor(aligned, flipped).sum()) / area)
    # A digitised perfect disc gives ~0.01-0.03; strongly lopsided shapes exceed 0.4.
    mean_ratio = float(np.mean(ratios))
    return _clip100((mean_ratio - 0.02) / 0.40 * 100.0)


def border_irregularity_score(mask: Mask) -> float:
    """Border irregularity from circularity, solidity and convexity-defect depth."""
    contour = _largest_contour(mask)
    area = cv2.contourArea(contour)
    # Smooth pixel staircase before measuring the perimeter so that a digitised circle
    # is not reported as "jagged".
    smoothed = cv2.approxPolyDP(contour, 1.0, True)
    perimeter = cv2.arcLength(smoothed, True)
    if area <= 0 or perimeter <= 0:
        return 0.0
    circularity = min(1.0, 4.0 * np.pi * area / perimeter**2)

    hull = cv2.convexHull(contour)
    hull_area = cv2.contourArea(hull)
    solidity = area / hull_area if hull_area > 0 else 1.0

    equivalent_diameter = float(np.sqrt(4.0 * area / np.pi))
    defect_depth = 0.0
    hull_idx = cv2.convexHull(contour, returnPoints=False)
    if hull_idx is not None and len(hull_idx) > 3:
        try:
            defects = cv2.convexityDefects(contour, hull_idx)
        except cv2.error:
            defects = None
        if defects is not None:
            depths = defects.reshape(-1, 4)[:, 3].astype(np.float64) / 256.0
            significant = depths[depths > 0.02 * equivalent_diameter]
            defect_depth = float(significant.sum()) / max(equivalent_diameter, 1.0)

    circ_term = min(1.0, (1.0 - circularity) / 0.55)
    solidity_term = min(1.0, (1.0 - solidity) / 0.25)
    defect_term = min(1.0, defect_depth / 0.8)
    return _clip100((0.45 * circ_term + 0.35 * solidity_term + 0.20 * defect_term) * 100.0)


def color_features(image: RGBImage, mask: Mask, max_clusters: int = 6) -> tuple[float, int]:
    """Colour variation (0-100) and number of perceptually distinct colour clusters."""
    pixels_rgb = image[mask > 0]
    if len(pixels_rgb) < 50:
        return 0.0, 0
    rng = np.random.default_rng(0)
    if len(pixels_rgb) > 6000:
        pixels_rgb = pixels_rgb[rng.choice(len(pixels_rgb), 6000, replace=False)]
    lab = skcolor.rgb2lab(pixels_rgb.reshape(-1, 1, 3) / 255.0).reshape(-1, 3).astype(np.float32)

    k = min(max_clusters, max(1, len(lab) // 100))
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.5)
    cv2.setRNGSeed(0)
    _, labels, centers = cv2.kmeans(lab, k, None, criteria, 3, cv2.KMEANS_PP_CENTERS)
    counts = np.bincount(labels.ravel(), minlength=k).astype(np.float64)

    # Merge clusters closer than a just-noticeable-ish difference (Delta E 76 < 15) and
    # ignore clusters covering under 5% of the spot.
    order = np.argsort(-counts)
    kept: list[tuple[NDArray[np.float32], float]] = []
    for idx in order:
        share = counts[idx] / counts.sum()
        centre = centers[idx]
        merged = False
        for j, (kept_centre, kept_share) in enumerate(kept):
            if float(np.linalg.norm(kept_centre - centre)) < 15.0:
                kept[j] = (kept_centre, kept_share + share)
                merged = True
                break
        if not merged and share >= 0.05:
            kept.append((centre, share))
    color_count = max(1, len(kept))

    spread = float(np.sqrt(lab.var(axis=0).sum()))  # overall Delta-E spread
    variation = (spread - 4.0) / 22.0 * 70.0 + (color_count - 1) * 12.0
    return _clip100(variation), color_count


def diameter_features(mask: Mask, scale_to_original: float) -> tuple[float, float]:
    contour = _largest_contour(mask)
    _, radius = cv2.minEnclosingCircle(contour)
    diameter = 2.0 * radius
    h, w = mask.shape
    relative = diameter / float(min(h, w)) * 100.0
    return round(diameter * scale_to_original, 1), _clip100(relative)


def cv_concern_score(features: LesionFeatures) -> float:
    """Combine features into a 0-100 visual-irregularity score (ABCD-style weighting)."""
    size_term = min(100.0, max(0.0, (features.diameter_relative - 25.0) / 50.0 * 100.0))
    score = (
        0.30 * features.asymmetry
        + 0.30 * features.border_irregularity
        + 0.32 * features.color_variation
        + 0.08 * size_term
    )
    return _clip100(score)


def analyze_image(image: RGBImage) -> CVAnalysis:
    """Run quality checks, segmentation and feature extraction on an RGB uint8 image."""
    if image.ndim != 3 or image.shape[2] != 3:
        raise ValueError("Expected an RGB image")
    work, scale = resize_for_analysis(image)
    quality = assess_quality(work)
    mask = segment_lesion(work)
    if mask is None:
        issues = [
            *quality.issues,
            "No distinct spot could be isolated. Centre the spot and fill about a third "
            "of the frame with it.",
        ]
        quality = QualityReport(False, quality.blur_score, quality.brightness, quality.contrast, issues)
        return CVAnalysis(quality=quality, features=EMPTY_FEATURES, segmented=False, cv_score=None)

    color_variation, color_count = color_features(work, mask)
    diameter_px, diameter_relative = diameter_features(mask, scale)
    features = LesionFeatures(
        asymmetry=asymmetry_score(mask),
        border_irregularity=border_irregularity_score(mask),
        color_variation=color_variation,
        diameter_px=diameter_px,
        diameter_relative=diameter_relative,
        color_count=color_count,
    )
    logger.debug("cv features", extra={"features": features.to_dict()})
    return CVAnalysis(quality, features, segmented=True, cv_score=cv_concern_score(features))
