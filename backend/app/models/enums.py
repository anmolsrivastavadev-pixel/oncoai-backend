"""String enums shared by models and schemas (stored as VARCHAR + CHECK constraints)."""

from __future__ import annotations

from enum import StrEnum


class Role(StrEnum):
    user = "user"
    moderator = "moderator"
    admin = "admin"


class ConcernLevel(StrEnum):
    low = "low"
    moderate = "moderate"
    higher = "higher"


class BodyLocation(StrEnum):
    head_neck = "head_neck"
    face = "face"
    scalp = "scalp"
    chest = "chest"
    abdomen = "abdomen"
    back = "back"
    upper_arm_left = "upper_arm_left"
    upper_arm_right = "upper_arm_right"
    forearm_left = "forearm_left"
    forearm_right = "forearm_right"
    hand_left = "hand_left"
    hand_right = "hand_right"
    thigh_left = "thigh_left"
    thigh_right = "thigh_right"
    lower_leg_left = "lower_leg_left"
    lower_leg_right = "lower_leg_right"
    foot_left = "foot_left"
    foot_right = "foot_right"
    other = "other"


class AppointmentStatus(StrEnum):
    booked = "booked"
    cancelled = "cancelled"
    completed = "completed"


class ReminderKind(StrEnum):
    rescan = "rescan"
    appointment = "appointment"
    self_check = "self_check"
    custom = "custom"


class PostTopic(StrEnum):
    support = "support"
    awareness = "awareness"
    prevention = "prevention"
    stories = "stories"
    questions = "questions"


class ContentStatus(StrEnum):
    visible = "visible"
    hidden = "hidden"  # auto-hidden pending moderator review (internal)
    removed = "removed"


class ReactionKind(StrEnum):
    support = "support"
    hug = "hug"
    strength = "strength"
    relate = "relate"


class ReportStatus(StrEnum):
    open = "open"
    dismissed = "dismissed"
    actioned = "actioned"


def check_in(column: str, enum: type[StrEnum]) -> str:
    values = ", ".join(f"'{member.value}'" for member in enum)
    return f"{column} IN ({values})"
