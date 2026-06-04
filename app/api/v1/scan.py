"""OncoAI Skin Lesion Analysis — Real Computer Vision Pipeline

This module performs actual image analysis using OpenCV and scikit-image.
It does NOT use any medical AI model. All analysis is computer-vision-based
pattern detection designed for educational awareness, not diagnosis.

What's real: image quality checks, lesion segmentation, ABCDE-inspired
feature extraction, edge detection, color analysis, asymmetry measurement.
What's not real: no dermatological AI model, no cancer detection, no diagnosis.
"""

import uuid
import os
import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim
from PIL import Image
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app import models, schemas
from app.api import deps

router = APIRouter()

UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# ─── QUALITY DETECTION ──────────────────────────────────────

def detect_blur(image: np.ndarray) -> float:
    """Laplacian variance — lower = blurrier. < 50 = blurry, > 500 = sharp."""
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    return cv2.Laplacian(gray, cv2.CV_64F).var()


def detect_lighting(image: np.ndarray) -> dict:
    """Return brightness and contrast metrics."""
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    brightness = float(np.mean(gray))
    contrast = float(np.std(gray))
    return {"brightness": brightness, "contrast": contrast, "is_dark": brightness < 60, "is_low_contrast": contrast < 35}


def quality_feedback(brightness: float, contrast: float, blur_score: float) -> list:
    tips = []
    if brightness < 60:
        tips.append("The image appears dark. Try using flash or moving to better lighting.")
    if blur_score < 100:
        tips.append("The image is blurry. Hold the camera steady and focus on the lesion.")
    if contrast < 35:
        tips.append("Low contrast detected. Ensure the lesion stands out from surrounding skin.")
    if brightness < 50:
        tips.append("Image is too dark for reliable analysis. Please retake in brighter conditions.")
    return tips


# ─── LESION SEGMENTATION ────────────────────────────────────

def segment_lesion(image: np.ndarray) -> tuple:
    """
    Segment the largest skin region using CLAHE + Otsu thresholding.
    Returns (contour, mask, success).
    """
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    blurred = cv2.GaussianBlur(enhanced, (5, 5), 0)
    _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel)

    contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None, cleaned, False

    largest = max(contours, key=cv2.contourArea)
    if cv2.contourArea(largest) < 500:
        return None, cleaned, False

    return largest, cleaned, True


# ─── ABCDE FEATURE EXTRACTION ───────────────────────────────

def analyze_asymmetry(image: np.ndarray, contour: np.ndarray) -> tuple:
    """
    Split lesion along vertical and horizontal axes, compare halves using SSIM.
    Returns (score 0-100, detail_string, recommendations).
    """
    x, y, w, h = cv2.boundingRect(contour)
    roi = image[y:y + h, x:x + w]
    if roi.size == 0 or w < 10:
        return 0.0, "Lesion too small to assess asymmetry.", []

    mask = np.zeros((h, w), dtype=np.uint8)
    shifted = contour - [x, y]
    cv2.drawContours(mask, [shifted], -1, 255, -1)

    gray = cv2.cvtColor(roi, cv2.COLOR_RGB2GRAY)
    gray = cv2.bitwise_and(gray, gray, mask=mask)

    mid_v = w // 2
    left = gray[:, :mid_v]
    right_flipped = cv2.flip(gray[:, mid_v:mid_v * 2] if w % 2 == 0 else gray[:, mid_v + 1:mid_v * 2 + 1], 1)
    min_w = min(left.shape[1], right_flipped.shape[1])
    if min_w < 3:
        return 0.0, "Lesion too small for asymmetry measurement.", []

    left = left[:, :min_w]
    right_flipped = right_flipped[:, :min_w]

    ssim_score = float(ssim(left, right_flipped, data_range=255))
    asymmetry = round((1.0 - ssim_score) * 100, 1)

    details = []
    if asymmetry < 20:
        details.append("The lesion appears relatively symmetric between left and right halves.")
    elif asymmetry < 40:
        details.append("Moderate asymmetry detected. The left and right halves show some variation.")
    else:
        details.append("Significant asymmetry detected. The two halves of the lesion differ noticeably.")

    recs = []
    if asymmetry > 25:
        recs.append("Asymmetry can be a warning sign — consider showing this to a dermatologist.")

    return asymmetry, " ".join(details), recs


def analyze_border(image: np.ndarray, contour: np.ndarray) -> tuple:
    """Analyze border irregularity using perimeter-to-area ratio."""
    area = cv2.contourArea(contour)
    perimeter = cv2.arcLength(contour, True)
    if area < 1 or perimeter < 1:
        return 0.0, "Cannot measure border.", []

    circularity = (4 * np.pi * area) / (perimeter * perimeter)
    irregularity = round((1.0 - min(circularity, 1.0)) * 100, 1)

    details = []
    if irregularity < 25:
        details.append("The lesion border appears relatively smooth and well-defined.")
    elif irregularity < 50:
        details.append("Some border irregularity detected. The outline is not perfectly smooth.")
    else:
        details.append("The border appears notably irregular or jagged.")

    recs = []
    if irregularity > 30:
        recs.append("Irregular borders can be a skin change pattern worth discussing with a professional.")

    return irregularity, " ".join(details), recs


def analyze_color(image: np.ndarray, contour: np.ndarray) -> tuple:
    """Use K-means clustering to count distinct color regions in the lesion."""
    x, y, w, h = cv2.boundingRect(contour)
    roi = image[y:y + h, x:x + w]
    if roi.size == 0:
        return 0.0, "Cannot analyze color.", []

    mask = np.zeros((h, w), dtype=np.uint8)
    shifted = contour - [x, y]
    cv2.drawContours(mask, [shifted], -1, 255, -1)

    pixels = roi[mask == 255].astype(np.float32)
    if len(pixels) < 50:
        return 0.0, "Too few pixels to analyze color.", []

    k = min(5, max(2, len(pixels) // 200))
    _, labels, centers = cv2.kmeans(pixels, k, None,
        (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0), 3, cv2.KMEANS_PP_CENTERS)

    std_colors = np.std(centers, axis=0)
    color_variation = round(float(np.mean(std_colors)) / 128.0 * 100, 1)

    details = []
    if color_variation < 20:
        details.append(f"The lesion shows relatively uniform coloring ({k} distinct tone{'s' if k > 1 else ''}).")
    elif color_variation < 45:
        details.append(f"Moderate color variation detected with {k} distinct tones.")
    else:
        details.append(f"Significant color variation across {k} color regions.")

    recs = []
    if color_variation > 35:
        recs.append("Multiple color tones can be educational to discuss with a specialist.")

    return color_variation, " ".join(details), recs


def estimate_diameter(contour: np.ndarray, image: np.ndarray) -> tuple:
    """Estimate lesion diameter using contour bounding box (pixels only — no mm calibration)."""
    x, y, w, h = cv2.boundingRect(contour)
    diameter_px = max(w, h)
    img_diag = np.sqrt(image.shape[0] ** 2 + image.shape[1] ** 2)
    mm_est = round((diameter_px / img_diag) * 35, 1)

    note = f"Estimated {diameter_px}px ({mm_est}mm approximate based on image dimensions). For accurate measurement, include a reference object like a coin."
    return mm_est, note


# ─── MAIN ENDPOINT ──────────────────────────────────────────

@router.post("/upload", response_model=schemas.scan.Scan)
async def upload_skin_image(
    *,
    db: Session = Depends(deps.get_db),
    current_user: models.user.User = Depends(deps.get_current_user),
    file: UploadFile = File(...)
) -> Any:
    """Upload a skin image for computer-vision-based pattern analysis."""
    allowed_types = ["image/jpeg", "image/png", "image/webp"]
    if file.content_type not in allowed_types and not file.filename.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
        raise HTTPException(status_code=400, detail="Invalid file type. Upload JPEG, PNG, or WebP.")

    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    try:
        pil_img = Image.open(file_path).convert('RGB')
        img = np.array(pil_img)
        h, w = img.shape[:2]

        # ─── Quality Analysis ─────────────────────────────
        blur_score = round(float(detect_blur(img)), 1)
        lighting = detect_lighting(img)
        tips = quality_feedback(lighting["brightness"], lighting["contrast"], blur_score)
        quality = round(min(100.0, max(10.0, (blur_score / 5) + (lighting["brightness"] / 2.55))), 1)

        # ─── Lesion Segmentation ──────────────────────────
        contour, mask, found = segment_lesion(img)

        features = []
        warnings = []
        asym = border = color_var = 0.0
        diam = None

        if found and contour is not None:
            asym, asym_detail, asym_recs = analyze_asymmetry(img, contour)
            features.append(asym_detail)
            warnings.extend(asym_recs)

            border, border_detail, border_recs = analyze_border(img, contour)
            features.append(border_detail)
            warnings.extend(border_recs)

            color_var, color_detail, color_recs = analyze_color(img, contour)
            features.append(color_detail)
            warnings.extend(color_recs)

            diam, diam_note = estimate_diameter(contour, img)
            features.append(diam_note)
        else:
            features.append("Could not isolate a distinct skin lesion. Try photographing closer with better lighting.")
            tips.append("No distinct lesion detected. Ensure the lesion fills the frame and the image is well-lit.")

        # ─── Build Educational Guidance ────────────────────
        overall_score = round((asym + border + color_var) / 3, 1)
        feature_detail = " | ".join(features)

        if not found:
            classification = "Insufficient Image Quality"
            confidence = quality
            guidance = "Unable to analyze. " + (" ".join(tips) if tips else "Please retake with better lighting and a closer view of the lesion.")
        elif overall_score < 25:
            classification = "Low Visual Variation"
            confidence = round(min(95.0, 75.0 + (100 - overall_score) * 0.2), 1)
            guidance = "The lesion shows relatively uniform visual patterns. Continue regular monitoring. " + (" ".join(warnings) if warnings else "")
        elif overall_score < 50:
            classification = "Moderate Visual Variation"
            confidence = round(60.0 + (50 - overall_score) * 0.4, 1)
            guidance = "Some visual variation detected. " + (" ".join(warnings) if warnings else "Consider professional review for peace of mind.")
        else:
            classification = "Significant Visual Variation"
            confidence = round(50.0 + (100 - overall_score) * 0.15, 1)
            guidance = "Multiple visual patterns detected. " + (" ".join(warnings) if warnings else "A dermatologist review is recommended.")
    except Exception as e:
        print(f"Analysis error: {e}")
        raise HTTPException(status_code=500, detail="Image analysis failed. Please try a different image.")

    db_obj = models.Scan(
        filename=unique_filename,
        classification=classification,
        confidence=float(confidence),
        guidance=guidance,
        quality_score=float(quality),
        asymmetry_score=float(asym),
        border_score=float(border),
        color_score=float(color_var),
        diameter_mm=float(diam) if diam else None,
        feature_details=feature_detail,
        user_id=current_user.id,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


@router.get("/history", response_model=List[schemas.scan.Scan])
def read_scan_history(
    db: Session = Depends(deps.get_db),
    current_user: models.user.User = Depends(deps.get_current_user),
) -> Any:
    return db.query(models.Scan).filter(
        models.Scan.user_id == current_user.id
    ).order_by(models.Scan.created_at.desc()).all()


@router.delete("/{scan_id}")
def delete_scan(
    scan_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.user.User = Depends(deps.get_current_user),
) -> Any:
    scan = db.query(models.Scan).filter(
        models.Scan.id == scan_id, models.Scan.user_id == current_user.id
    ).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    file_path = os.path.join(UPLOAD_DIR, scan.filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    db.delete(scan)
    db.commit()
    return {"detail": "Scan deleted"}


@router.get("/compare/{scan_id_1}/{scan_id_2}")
def compare_scans(
    scan_id_1: int,
    scan_id_2: int,
    db: Session = Depends(deps.get_db),
    current_user: models.user.User = Depends(deps.get_current_user),
) -> Any:
    """Compare two scans and detect visual changes over time."""
    s1 = db.query(models.Scan).filter(
        models.Scan.id == scan_id_1, models.Scan.user_id == current_user.id
    ).first()
    s2 = db.query(models.Scan).filter(
        models.Scan.id == scan_id_2, models.Scan.user_id == current_user.id
    ).first()
    if not s1 or not s2:
        raise HTTPException(status_code=404, detail="One or both scans not found")

    p1 = os.path.join(UPLOAD_DIR, s1.filename)
    p2 = os.path.join(UPLOAD_DIR, s2.filename)
    if not os.path.exists(p1) or not os.path.exists(p2):
        raise HTTPException(status_code=404, detail="Image files not found on disk")

    img1 = cv2.imread(p1, cv2.IMREAD_GRAYSCALE)
    img2 = cv2.imread(p2, cv2.IMREAD_GRAYSCALE)
    img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))

    sim = round(float(ssim(img1, img2, data_range=255)) * 100, 1)
    changed = sim < 85

    border_delta = round(abs((s2.border_score or 0) - (s1.border_score or 0)), 1)
    asym_delta = round(abs((s2.asymmetry_score or 0) - (s1.asymmetry_score or 0)), 1)

    notes = f"Overall similarity: {sim}%. "
    if changed:
        notes += "Noticeable visual change detected between these scans. "
    else:
        notes += "Scans appear visually similar. "
    if border_delta > 5:
        notes += f"Border pattern changed by {border_delta}%. "
    if asym_delta > 5:
        notes += f"Asymmetry changed by {asym_delta}%. "
    notes += "This is an automated visual comparison, not a medical assessment."

    return {
        "scan_id_1": scan_id_1,
        "scan_id_2": scan_id_2,
        "similarity": sim,
        "change_detected": changed,
        "notes": notes,
    }
