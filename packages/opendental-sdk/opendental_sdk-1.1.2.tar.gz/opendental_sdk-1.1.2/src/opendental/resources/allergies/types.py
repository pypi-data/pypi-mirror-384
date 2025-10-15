"""Allergy types and enums for Open Dental SDK."""

from enum import Enum


class AllergySeverity(str, Enum):
    """Allergy severity enum."""
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    UNKNOWN = "unknown"


class AllergyType(str, Enum):
    """Allergy type enum."""
    DRUG = "drug"
    FOOD = "food"
    ENVIRONMENTAL = "environmental"
    CONTACT = "contact"
    OTHER = "other"


class AllergyStatus(str, Enum):
    """Allergy status enum."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    RESOLVED = "resolved"