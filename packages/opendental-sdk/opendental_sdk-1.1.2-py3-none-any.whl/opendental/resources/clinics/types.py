"""Clinic types and enums for Open Dental SDK."""

from enum import Enum


class ClinicType(str, Enum):
    """Clinic type enum."""
    DENTAL = "dental"
    MEDICAL = "medical"
    ORTHODONTIC = "orthodontic"
    ORAL_SURGERY = "oral_surgery"
    PEDIATRIC = "pediatric"
    PERIODONTIC = "periodontic"
    ENDODONTIC = "endodontic"
    PROSTHODONTIC = "prosthodontic"
    OTHER = "other"


class ClinicStatus(str, Enum):
    """Clinic status enum."""
    ACTIVE = "active"
    HIDDEN = "hidden"
    INACTIVE = "inactive"