"""Clearly FICTIONAL sample dermatologist listings.

Every name, clinic, address and phone number below is invented for demonstration. Phone
numbers use ranges reserved for fiction where they exist (UK Ofcom 020 7946 0xxx, US
555-01xx) and an obviously invalid all-zero pattern for India. All rows are flagged
``is_sample=True`` so the UI can show a "Sample listing" badge.
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Dermatologist

logger = logging.getLogger(__name__)

SAMPLE_DERMATOLOGISTS: list[dict[str, Any]] = [
    {
        "name": "Dr. Eleanor Whitcombe",
        "title": "Consultant Dermatologist (sample)",
        "specialty": "Skin cancer screening",
        "clinic_name": "Northside Skin Clinic (sample)",
        "city": "London",
        "address": "12 Sample Row, London (sample address)",
        "phone": "+44 20 7946 0101",
        "timezone": "Europe/London",
        "rating": 4.8,
        "review_count": 212,
        "languages": ["English", "French"],
        "accepts_new_patients": True,
        "bio": "Sample profile: focuses on mole checks and skin self-examination education.",
    },
    {
        "name": "Dr. Rohan Castellino",
        "title": "Consultant Dermatologist (sample)",
        "specialty": "General dermatology",
        "clinic_name": "Riverside Dermatology Rooms (sample)",
        "city": "London",
        "address": "48 Example Lane, London (sample address)",
        "phone": "+44 20 7946 0102",
        "timezone": "Europe/London",
        "rating": 4.6,
        "review_count": 154,
        "languages": ["English", "Hindi", "Konkani"],
        "accepts_new_patients": True,
        "bio": "Sample profile: general skin health consultations and annual skin checks.",
    },
    {
        "name": "Dr. Harriet Quenby",
        "title": "Dermatologist (sample)",
        "specialty": "Mole mapping",
        "clinic_name": "Pennine Skin Centre (sample)",
        "city": "Manchester",
        "address": "7 Placeholder Street, Manchester (sample address)",
        "phone": "+44 20 7946 0103",
        "timezone": "Europe/London",
        "rating": 4.7,
        "review_count": 98,
        "languages": ["English"],
        "accepts_new_patients": True,
        "bio": "Sample profile: total-body photography and long-term mole monitoring.",
    },
    {
        "name": "Dr. Callum Ardrossan",
        "title": "Consultant Dermatologist (sample)",
        "specialty": "Paediatric dermatology",
        "clinic_name": "Lothian Family Skin Practice (sample)",
        "city": "Edinburgh",
        "address": "3 Fictional Close, Edinburgh (sample address)",
        "phone": "+44 20 7946 0104",
        "timezone": "Europe/London",
        "rating": 4.5,
        "review_count": 76,
        "languages": ["English", "Scottish Gaelic"],
        "accepts_new_patients": False,
        "bio": "Sample profile: skin health for children and families.",
    },
    {
        "name": "Dr. Ananya Varadkar",
        "title": "Consultant Dermatologist (sample)",
        "specialty": "Skin cancer screening",
        "clinic_name": "Harbourview Skin Clinic (sample)",
        "city": "Mumbai",
        "address": "21 Demo Marg, Mumbai (sample address)",
        "phone": "+91 00000 00001",
        "timezone": "Asia/Kolkata",
        "rating": 4.9,
        "review_count": 341,
        "languages": ["English", "Hindi", "Marathi"],
        "accepts_new_patients": True,
        "bio": "Sample profile: skin checks and sun-safety education.",
    },
    {
        "name": "Dr. Kabir Malhotrani",
        "title": "Dermatologist (sample)",
        "specialty": "General dermatology",
        "clinic_name": "Capital Skin Care Studio (sample)",
        "city": "Delhi",
        "address": "9 Example Enclave, New Delhi (sample address)",
        "phone": "+91 00000 00002",
        "timezone": "Asia/Kolkata",
        "rating": 4.4,
        "review_count": 187,
        "languages": ["English", "Hindi", "Punjabi"],
        "accepts_new_patients": True,
        "bio": "Sample profile: general dermatology and skin-type specific sun care advice.",
    },
    {
        "name": "Dr. Meera Iyengarth",
        "title": "Consultant Dermatologist (sample)",
        "specialty": "Dermatologic surgery",
        "clinic_name": "Garden City Dermatology (sample)",
        "city": "Bengaluru",
        "address": "55 Sample Road, Bengaluru (sample address)",
        "phone": "+91 00000 00003",
        "timezone": "Asia/Kolkata",
        "rating": 4.7,
        "review_count": 129,
        "languages": ["English", "Kannada", "Tamil"],
        "accepts_new_patients": True,
        "bio": "Sample profile: procedural dermatology and post-procedure skin care education.",
    },
    {
        "name": "Dr. Sundar Pallavaram",
        "title": "Dermatologist (sample)",
        "specialty": "Mole mapping",
        "clinic_name": "Coromandel Skin Institute (sample)",
        "city": "Chennai",
        "address": "14 Placeholder Salai, Chennai (sample address)",
        "phone": "+91 00000 00004",
        "timezone": "Asia/Kolkata",
        "rating": 4.6,
        "review_count": 88,
        "languages": ["English", "Tamil", "Telugu"],
        "accepts_new_patients": True,
        "bio": "Sample profile: digital dermoscopy follow-up and mole tracking.",
    },
    {
        "name": "Dr. Juliana Brightwater",
        "title": "Board-certified Dermatologist (sample)",
        "specialty": "Skin cancer screening",
        "clinic_name": "Hudson Skin Health Group (sample)",
        "city": "New York",
        "address": "100 Example Ave, New York, NY (sample address)",
        "phone": "+1 212-555-0101",
        "timezone": "America/New_York",
        "rating": 4.8,
        "review_count": 403,
        "languages": ["English", "Spanish"],
        "accepts_new_patients": True,
        "bio": "Sample profile: full-body skin exams and skin cancer awareness education.",
    },
    {
        "name": "Dr. Marcus Okonkwo-Hale",
        "title": "Board-certified Dermatologist (sample)",
        "specialty": "General dermatology",
        "clinic_name": "Lakeshore Dermatology (sample)",
        "city": "Chicago",
        "address": "250 Sample Street, Chicago, IL (sample address)",
        "phone": "+1 312-555-0102",
        "timezone": "America/Chicago",
        "rating": 4.5,
        "review_count": 167,
        "languages": ["English", "Igbo"],
        "accepts_new_patients": True,
        "bio": "Sample profile: skin health across all skin types and tones.",
    },
    {
        "name": "Dr. Priya Delacroix",
        "title": "Dermatologist (sample)",
        "specialty": "Cosmetic and medical dermatology",
        "clinic_name": "Hill Country Skin Studio (sample)",
        "city": "Austin",
        "address": "42 Demo Blvd, Austin, TX (sample address)",
        "phone": "+1 512-555-0103",
        "timezone": "America/Chicago",
        "rating": 4.3,
        "review_count": 59,
        "languages": ["English", "Tamil", "French"],
        "accepts_new_patients": False,
        "bio": "Sample profile: medical and cosmetic dermatology consultations.",
    },
    {
        "name": "Dr. Theodore Rainier-Moss",
        "title": "Board-certified Dermatologist (sample)",
        "specialty": "Mole mapping",
        "clinic_name": "Puget Sound Skin Clinic (sample)",
        "city": "Seattle",
        "address": "8 Fictional Way, Seattle, WA (sample address)",
        "phone": "+1 206-555-0104",
        "timezone": "America/Los_Angeles",
        "rating": 4.7,
        "review_count": 118,
        "languages": ["English", "Japanese"],
        "accepts_new_patients": True,
        "bio": "Sample profile: mole surveillance and UV-protection education.",
    },
]


def seed_dermatologists(db: Session) -> int:
    """Insert missing sample listings (idempotent). Returns how many were inserted."""
    existing = set(db.scalars(select(Dermatologist.name)).all())
    added = 0
    for data in SAMPLE_DERMATOLOGISTS:
        if data["name"] in existing:
            continue
        db.add(Dermatologist(is_sample=True, **data))
        added += 1
    if added:
        db.commit()
        logger.info("seeded sample dermatologists", extra={"count": added})
    return added
