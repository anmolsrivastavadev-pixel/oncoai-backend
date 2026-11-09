"""Import every model so Base.metadata is complete (used by Alembic and tests)."""

from app.models.appointment import Appointment
from app.models.community import Comment, Post, Reaction, Report
from app.models.dermatologist import Dermatologist
from app.models.lesion import Lesion
from app.models.reminder import Reminder
from app.models.scan import Scan
from app.models.symptom_log import SymptomLog
from app.models.user import User

__all__ = [
    "Appointment",
    "Comment",
    "Dermatologist",
    "Lesion",
    "Post",
    "Reaction",
    "Reminder",
    "Report",
    "Scan",
    "SymptomLog",
    "User",
]
