"""Turn analyzer output into an educational concern level and user-facing wording.

Safety rules enforced here:
* Only three educational concern levels exist: low / moderate / higher.
* Wording describes *visual patterns* only. No disease names, no diagnosis, no
  treatment. Model class names/probabilities are never included in the output.
* Poor photo quality never produces a reassuring "low" result (see ``_apply_quality_floor``).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.ml.analyzer import AnalysisResult
from app.models.enums import ConcernLevel

LOW_MAX = 35.0
MODERATE_MAX = 65.0

MODEL_WEIGHT = 0.6
CV_WEIGHT = 0.4
# Used when no spot could be segmented and there is no model signal either.
UNKNOWN_CV_SCORE = 40.0

SYMPTOM_BUMPS: dict[str, float] = {
    "bleeding": 12.0,
    "changed_size": 8.0,
    "changed_color": 8.0,
    "changed_shape": 8.0,
    "new_spot": 5.0,
    "itching": 2.0,
    "pain": 2.0,
}
MAX_SYMPTOM_BUMP = 25.0

SYMPTOM_PHRASES = {
    "bleeding": "bleeding",
    "changed_size": "a change in size",
    "changed_color": "a change in colour",
    "changed_shape": "a change in shape",
    "new_spot": "that this is a new spot",
    "itching": "itching",
    "pain": "pain or tenderness",
}

HEADLINES = {
    ConcernLevel.low: "No prominent irregular visual patterns detected.",
    ConcernLevel.moderate: "Some irregular visual patterns detected.",
    ConcernLevel.higher: (
        "Irregular visual patterns detected. Consider professional dermatologist evaluation."
    ),
}
POOR_QUALITY_HEADLINE = (
    "Photo quality is too low for a reliable visual check. Retake the photo in good light."
)

CONSULT = "Consider professional dermatologist evaluation."
RETAKE = "Retake the photo in good light."


@dataclass(frozen=True)
class ConcernReport:
    level: ConcernLevel
    score: float
    headline: str
    observations: list[str]
    recommendations: list[str]
    audit: dict[str, Any] = field(default_factory=dict)


def level_for(score: float) -> ConcernLevel:
    if score < LOW_MAX:
        return ConcernLevel.low
    if score < MODERATE_MAX:
        return ConcernLevel.moderate
    return ConcernLevel.higher


def symptom_bump(symptoms: dict[str, Any] | None) -> float:
    if not symptoms:
        return 0.0
    total = sum(bump for key, bump in SYMPTOM_BUMPS.items() if symptoms.get(key))
    return min(MAX_SYMPTOM_BUMP, total)


def base_score(result: AnalysisResult) -> float:
    cv_score = result.cv.cv_score
    if result.model_score is not None:
        if cv_score is None:
            # No segmentation: rely on the model but never below the "unknown" prior.
            return max(result.model_score, UNKNOWN_CV_SCORE)
        return MODEL_WEIGHT * result.model_score + CV_WEIGHT * cv_score
    return cv_score if cv_score is not None else UNKNOWN_CV_SCORE


def _feature_observations(result: AnalysisResult) -> list[str]:
    if not result.cv.segmented:
        return ["A distinct spot could not be isolated in this photo."]
    f = result.cv.features
    notes: list[str] = []
    if f.asymmetry >= 50:
        notes.append("The two halves of the spot look noticeably different in shape.")
    elif f.asymmetry >= 25:
        notes.append("The spot's shape is somewhat uneven between its halves.")
    if f.border_irregularity >= 50:
        notes.append("The border looks irregular or uneven.")
    elif f.border_irregularity >= 25:
        notes.append("Parts of the border look slightly uneven.")
    if f.color_count >= 3 or f.color_variation >= 50:
        notes.append("Several different colour tones are visible within the spot.")
    elif f.color_variation >= 25:
        notes.append("Some variation in colour tone is visible within the spot.")
    if not notes:
        notes.append("Shape, border and colour look fairly even in this photo.")
    return notes


def _apply_quality_floor(score: float, level: ConcernLevel, quality_ok: bool) -> tuple[float, ConcernLevel]:
    """A poor photo must not yield a falsely reassuring result.

    If the quality checks fail we floor the result at "moderate" (score >= LOW_MAX):
    we can't tell the user "no irregular patterns" from a blurry or dark photo.
    """
    if quality_ok or level != ConcernLevel.low:
        return score, level
    return LOW_MAX, ConcernLevel.moderate


def build_report(result: AnalysisResult, symptoms: dict[str, Any] | None) -> ConcernReport:
    raw = base_score(result)
    bump = symptom_bump(symptoms)
    score = round(min(100.0, max(0.0, raw + bump)), 1)
    level = level_for(score)
    quality_ok = result.cv.quality.ok
    score, level = _apply_quality_floor(score, level, quality_ok)

    headline = HEADLINES[level] if quality_ok else POOR_QUALITY_HEADLINE

    observations: list[str] = []
    if level == ConcernLevel.higher:
        observations.append("Irregular visual patterns detected.")
    elif level == ConcernLevel.moderate and quality_ok:
        observations.append("Some irregular visual patterns detected.")
    elif level == ConcernLevel.low:
        observations.append("No prominent irregular visual patterns detected.")
    observations.extend(_feature_observations(result))
    if result.model_score is not None and result.model_score >= 50:
        observations.append("The image-pattern model flagged visual features worth a closer look.")
    reported = [phrase for key, phrase in SYMPTOM_PHRASES.items() if symptoms and symptoms.get(key)]
    if reported:
        observations.append(
            "You reported " + ", ".join(reported) + ". Changes like these are worth "
            "mentioning to a dermatologist."
        )

    recommendations: list[str] = []
    if not quality_ok:
        recommendations.append(RETAKE)
        recommendations.extend(result.cv.quality.issues)
    if level in (ConcernLevel.moderate, ConcernLevel.higher):
        recommendations.append(CONSULT)
    if level == ConcernLevel.higher:
        recommendations.append(
            "If the spot is new, changing, bleeding or itchy, try to arrange an appointment soon."
        )
    if symptoms and symptoms.get("bleeding"):
        recommendations.append(
            "If a spot bleeds without injury or a sore does not heal within a few weeks, "
            "contact a healthcare professional promptly."
        )
    if level == ConcernLevel.low:
        recommendations.append("Keep doing regular monthly skin self-checks.")
        recommendations.append(
            "See a dermatologist if you notice any change in size, shape or colour, or if "
            "anything about the spot concerns you."
        )
    recommendations.append(
        "Re-scan this spot in about 4 weeks in similar lighting to track any changes."
    )

    audit = {
        "base_score": round(raw, 2),
        "symptom_bump": bump,
        "cv_score": result.cv.cv_score,
        "model_score": result.model_score,
        "quality_ok": quality_ok,
        "probabilities": result.probabilities,
    }
    return ConcernReport(level, score, headline, _dedupe(observations), _dedupe(recommendations), audit)


def _dedupe(items: list[str]) -> list[str]:
    return list(dict.fromkeys(items))
