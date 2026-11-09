"""Community content filters: privacy (contact details) and profanity masking."""

from __future__ import annotations

import re

AUTO_HIDE_REPORTS = 3
ANONYMOUS_NAME = "Anonymous member"

_EMAIL = re.compile(
    r"[\w.+-]+\s*(?:@|\(at\)|\[at\]|\sat\s)\s*[\w-]+(?:\s*(?:\.|\(dot\)|\[dot\]|\sdot\s)\s*[\w-]+)*"
    r"\s*(?:\.|\(dot\)|\[dot\]|\sdot\s)\s*[a-z]{2,24}\b",
    re.IGNORECASE,
)
# 9-15 digits optionally separated by spaces, dots, dashes or parentheses, optional "+".
_PHONE = re.compile(r"(?<![\w])\+?(?:\d[\s().-]{0,2}){8,14}\d(?![\w])")

PRIVACY_MESSAGE = (
    "For your safety, posts and comments can't include email addresses or phone numbers. "
    "Please remove contact details and try again."
)

PROFANITY = frozenset(
    {
        "arse", "arsehole", "asshole", "bastard", "bitch", "bitches", "bollocks", "bullshit",
        "cock", "cunt", "dick", "dickhead", "fuck", "fucked", "fucker", "fucking", "fucks",
        "motherfucker", "piss", "pissed", "prick", "shit", "shits", "shitty", "slut",
        "twat", "wanker", "whore",
    }
)
_WORD = re.compile(r"[A-Za-z]+")


def contains_contact_details(text: str) -> bool:
    if _EMAIL.search(text):
        return True
    for match in _PHONE.finditer(text):
        digits = sum(ch.isdigit() for ch in match.group(0))
        if 9 <= digits <= 15:
            return True
    return False


def mask_profanity(text: str) -> str:
    def replace(match: re.Match[str]) -> str:
        word = match.group(0)
        if word.lower() in PROFANITY:
            return word[0] + "*" * (len(word) - 1)
        return word

    return _WORD.sub(replace, text)


def display_name(full_name: str) -> str:
    """First name plus last initial, e.g. "Priya S." (limits identifiability)."""
    parts = full_name.split()
    if not parts:
        return "Member"
    if len(parts) == 1:
        return parts[0]
    return f"{parts[0]} {parts[-1][0].upper()}."
