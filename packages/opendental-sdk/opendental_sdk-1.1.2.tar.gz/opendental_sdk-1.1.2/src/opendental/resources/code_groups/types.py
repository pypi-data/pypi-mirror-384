"""Code groups types and enums for Open Dental SDK."""

from enum import Enum


class CodeGroupFixed(str, Enum):
    """Fixed code group types."""
    NONE = "None"
    BW = "BW"  # Bitewings
    PANO = "Pano"  # Panoramic
    BWPano = "BWPano"  # Bitewings and Panoramic
    PERIO_MAINT = "PerioMaint"  # Periodontal Maintenance
    DENT_PROPHY = "DentProphy"  # Dental Prophylaxis
    PERIO_SCALING = "PerioScaling"  # Periodontal Scaling
    LIMITED_EXAM = "LimitedExam"  # Limited Exam
    PA = "PA"  # Periapical
    COMP_EXAM = "CompExam"  # Comprehensive Exam
    FULL_SERIES = "FullSeries"  # Full Series