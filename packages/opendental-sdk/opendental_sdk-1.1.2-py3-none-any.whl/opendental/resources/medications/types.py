"""Medication types and enums for Open Dental SDK."""

from enum import Enum


class MedicationStatus(str, Enum):
    """Medication status enum."""
    ACTIVE = "active"
    DISCONTINUED = "discontinued"
    INACTIVE = "inactive"


class DosageUnit(str, Enum):
    """Dosage unit enum."""
    MG = "mg"
    ML = "ml"
    G = "g"
    UNIT = "unit"
    TABLET = "tablet"
    CAPSULE = "capsule"
    TEASPOON = "teaspoon"
    TABLESPOON = "tablespoon"
    DROP = "drop"
    PUFF = "puff"
    OTHER = "other"


class MedicationType(str, Enum):
    """Medication type enum."""
    PRESCRIPTION = "prescription"
    OVER_THE_COUNTER = "over_the_counter"
    SUPPLEMENT = "supplement"
    HERBAL = "herbal"
    OTHER = "other"