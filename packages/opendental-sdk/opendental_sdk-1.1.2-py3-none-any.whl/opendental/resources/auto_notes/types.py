"""Auto notes types and enums for Open Dental SDK."""

from enum import Enum


class AutoNoteCategory(str, Enum):
    """Auto note category enum."""
    GENERAL = "general"
    EXAM = "exam"
    TREATMENT = "treatment"
    PROGRESS = "progress"
    HYGIENE = "hygiene"
    PERIO = "perio"
    SURGERY = "surgery"
    CONSULTATION = "consultation"
    CUSTOM = "custom"


class AutoNoteType(str, Enum):
    """Auto note type enum."""
    TEMPLATE = "template"
    QUICK_NOTE = "quick_note"
    PROCEDURE_NOTE = "procedure_note"
    PROGRESS_NOTE = "progress_note"