"""Deterministic safety guardrails for the assistant.

Input guardrails run BEFORE any model call; matching requests get a fixed safe answer.
The output guardrail post-filters model text for diagnostic or treatment language.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.services.assistant.knowledge_base import NHS_111, NHS_MOLES, Source

SELF_HARM = "self_harm"
URGENT = "urgent_symptoms"
DIAGNOSIS = "diagnosis_request"
TREATMENT = "treatment_request"
OUTPUT_FILTERED = "output_filtered"


def _rx(*patterns: str) -> re.Pattern[str]:
    return re.compile("|".join(f"(?:{p})" for p in patterns), re.IGNORECASE)


_SELF_HARM = _rx(
    r"\b(kill|hurt|harm|cut)(ing)?\s+my\s?self\b",
    r"\bsuicid",
    r"\bself[\s-]?harm",
    r"\bend(ing)?\s+(my\s+(own\s+)?life|it\s+all)\b",
    r"\b(want|wanna|going)\s+to\s+die\b",
    r"\bdon'?t\s+want\s+to\s+(live|be\s+alive|be\s+here)",
    r"\bno\s+reason\s+to\s+live\b",
    r"\bbetter\s+off\s+dead\b",
)
_URGENT = _rx(
    r"\bbleed(ing|s)?\b.{0,40}\b(won'?t|will\s+not|doesn'?t|does\s+not|can'?t|cannot)\s+stop",
    r"\b(won'?t|can'?t|cannot)\s+stop\s+(the\s+)?bleed",
    r"\bbleed(ing|s)?\s+(a\s+lot|heavily|profusely|badly|non[\s-]?stop)",
    r"\b(heavy|severe|lots\s+of)\s+bleeding\b",
    r"\b(rapidly|quickly|fast)\s+(growing|spreading|getting\s+bigger|swelling)",
    r"\bgrowing\s+(really\s+|very\s+)?(fast|quickly|rapidly)",
    r"\bspreading\s+red(ness)?\b",
    r"\b(high\s+)?fever\b",
    r"\b(severe|unbearable|excruciating)\s+pain\b",
    r"\b(can'?t|cannot|trouble|difficulty)\s+breath",
    r"\bchest\s+pain\b",
    r"\bfaint(ed|ing)?\b|\bpassed\s+out\b|\bconfus(ed|ion)\b",
    r"\bblister(s|ing)?\s+(all\s+over|everywhere)",
)
_DIAGNOSIS = _rx(
    r"\b(do|could|might|may)\s+i\s+have\s+(skin\s+)?(cancer|melanoma|carcinoma|a\s+tumou?r)",
    r"\b(is|could|might)\s+(this|it|that|my\s+\w+)\s+(be\s+)?(a\s+)?(skin\s+)?(cancer(ous)?|melanoma|malignant|benign|carcinoma|tumou?r|dangerous|serious)",
    r"\bam\s+i\s+(dying|going\s+to\s+die|sick)",
    r"\bdiagnos(e|is|ing)\b",
    r"\bwhat\s+(is|'s)\s+(this|that|it|my)\s*(spot|mole|lesion|rash|lump|bump|mark|growth)?\s*\??$",
    r"\bwhat\s+(kind|type)\s+of\s+(spot|mole|lesion|rash|growth|cancer)\s+(is|do)",
    r"\b(is|does)\s+(my|this|the)\s+(scan|result|spot|mole)\s+(mean|show)\s+(i\s+have\s+)?(cancer|melanoma)",
    r"\btell\s+me\s+if\s+(it|this)\s+is\s+(cancer|melanoma|benign|malignant)",
    r"\bmelanoma\s*\?",
)
_TREATMENT = _rx(
    r"\b(how\s+(do|can|should)\s+i|what\s+(should|can)\s+i\s+(use|do)\s+to)\s+(treat|cure|get\s+rid\s+of|remove|heal)\b",
    r"\btreat(ment|ments|ing)?\s+(for|of)\b",
    r"\bcure\b",
    r"\b(medication|medicine|meds|drug|drugs|pill|pills|tablet|tablets|antibiotic|antibiotics|prescription|prescribe)\b",
    r"\b(dosage|dose|doses|how\s+many\s+mg|\d+\s*mg)\b",
    r"\bshould\s+i\s+take\b",
    r"\b(cream|ointment|gel)\s+(for|on|to\s+put\s+on)\s+(my|this|the|a)\s+(mole|spot|lesion|rash|growth|sore)",
    r"\bremove\s+(it|this|my\s+mole|the\s+mole|a\s+mole)\s+(at\s+home|myself|by\s+myself)",
    r"\b(chemo(therapy)?|radiotherapy|immunotherapy|surgery)\b",
    r"\bhome\s+remed(y|ies)\b",
)

_OUTPUT_BLOCK = _rx(
    r"\byou\s+(definitely\s+|probably\s+|likely\s+|most\s+likely\s+|may\s+|might\s+|could\s+)?(have|'ve\s+got|got)\s+(a\s+|an\s+)?(\w+\s+){0,3}(cancer|melanoma|carcinoma|tumou?r|keratos[ie]s|nev(us|i)|naev(us|i)|dermatofibroma|disease|infection|condition)",
    r"\b(this|it|that|the\s+spot|the\s+mole|your\s+\w+)\s+(is|looks\s+like|appears\s+to\s+be|seems\s+to\s+be)\s+(a\s+|an\s+)?(\w+\s+){0,2}(cancer(ous)?|melanoma|carcinoma|malignant|benign|tumou?r|keratosis|nevus|naevus)",
    r"\b(melanoma|carcinoma|basal\s+cell|squamous\s+cell|keratos[ie]s|dermatofibroma|merkel)\b",
    r"\byou\s+should\s+take\b",
    r"\btake\s+\d+\s*(mg|milligrams?|tablets?|pills?)\b",
    r"\b\d+\s*mg\b",
    r"\b(imiquimod|fluorouracil|5-?fu|efudex|vismodegib|sonidegib|pembrolizumab|nivolumab|ipilimumab|cemiplimab|dabrafenib|trametinib|vemurafenib|methotrexate|isotretinoin|tretinoin|hydrocortisone|prednisone|prednisolone|ibuprofen|paracetamol|acetaminophen|aspirin|antibiotics?|steroid\s+cream)\b",
    r"\b(nothing|no\s+need)\s+to\s+worry\b",
    r"\byou\s+(don'?t|do\s+not)\s+need\s+(to\s+see\s+)?(a\s+)?(doctor|dermatologist|gp)",
    r"\b(i|we)\s+(can\s+)?diagnose\b",
    r"\b(my|the)\s+diagnosis\s+is\b",
    r"\breplaces?\s+(your|a|the\s+need\s+for\s+a)\s+(doctor|dermatologist)",
)


@dataclass(frozen=True)
class GuardrailResponse:
    reason: str
    reply: str
    sources: list[Source] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)


CRISIS = GuardrailResponse(
    reason=SELF_HARM,
    reply=(
        "I'm really sorry you're feeling this way. You don't have to go through it alone, and "
        "talking to someone can help right now.\n\n"
        "If you are in immediate danger or might act on these thoughts, please call your local "
        "emergency number (999 in the UK, 911 in the US, 112 in the EU, 112 in India) or go to "
        "the nearest emergency department.\n\n"
        "You can also reach a crisis line any time:\n"
        "- US: call or text 988 (988 Suicide & Crisis Lifeline)\n"
        "- UK & Ireland: call Samaritans free on 116 123\n"
        "- Elsewhere: your local emergency number, or a local crisis helpline\n\n"
        "If you can, reach out to someone you trust and let them know how you're feeling."
    ),
    sources=[
        Source("988 Suicide & Crisis Lifeline", "https://988lifeline.org/"),
        Source("Samaritans", "https://www.samaritans.org/"),
    ],
    suggestions=[],
)

URGENT_RESPONSE = GuardrailResponse(
    reason=URGENT,
    reply=(
        "What you're describing should be checked by a healthcare professional promptly. "
        "Please contact a doctor or urgent care service now - for example NHS 111 in the UK, "
        "an urgent care clinic, or your GP. If symptoms are severe (heavy bleeding that won't "
        "stop with firm pressure, difficulty breathing, chest pain, fainting or confusion), "
        "call your local emergency number (999 UK, 911 US, 112 EU/India).\n\n"
        "OncoAI can't assess urgent symptoms, so please don't wait for an app result."
    ),
    sources=[NHS_111, NHS_MOLES],
    suggestions=["When should I seek medical help for a skin change?"],
)

DIAGNOSIS_RESPONSE = GuardrailResponse(
    reason=DIAGNOSIS,
    reply=(
        "I can't tell you what a spot is or whether it is harmful - only a qualified clinician "
        "who examines it can do that, and OncoAI is not able to diagnose. What I can do is help "
        "you understand the visual patterns doctors look for and when it's worth getting a "
        "spot checked.\n\n"
        "If a spot is new, changing in size, shape or colour, bleeding, itchy, or simply "
        "worrying you, please consider professional dermatologist evaluation. You can use the "
        "Dermatologists section of the app to find a clinic and book an appointment."
    ),
    sources=[NHS_MOLES],
    suggestions=[
        "What is the ABCDE rule?",
        "What does my scan result mean?",
        "What happens at a dermatologist appointment?",
    ],
)

TREATMENT_RESPONSE = GuardrailResponse(
    reason=TREATMENT,
    reply=(
        "I'm not able to recommend treatments, medicines, creams or doses - those decisions "
        "need a doctor or pharmacist who knows your health history and has examined the skin. "
        "Please don't try to remove or treat a mole or spot yourself.\n\n"
        "A GP or dermatologist can explain the options that are right for you. I'm happy to "
        "help with general skin-health education, like sun protection or how to check your skin."
    ),
    sources=[NHS_MOLES],
    suggestions=[
        "What happens at a dermatologist appointment?",
        "How do I protect my skin from the sun?",
    ],
)

OUTPUT_REDIRECT = (
    "I can't assess or name what a particular spot is, or recommend treatments or medicines. "
    "For anything specific to your skin, please consider professional dermatologist evaluation."
)


def check_input(text: str) -> GuardrailResponse | None:
    """Return a deterministic safe response if the message needs one, else None."""
    if _SELF_HARM.search(text):
        return CRISIS
    if _URGENT.search(text):
        return URGENT_RESPONSE
    if _TREATMENT.search(text):
        return TREATMENT_RESPONSE
    if _DIAGNOSIS.search(text):
        return DIAGNOSIS_RESPONSE
    return None


def output_violates(text: str) -> bool:
    return bool(_OUTPUT_BLOCK.search(text))
