"""Carrier types and enums for Open Dental SDK."""

from enum import Enum


class CarrierType(str, Enum):
    """Carrier type enum."""
    DENTAL = "dental"
    MEDICAL = "medical"
    VISION = "vision"
    ORTHODONTIC = "orthodontic"
    OTHER = "other"


class CarrierStatus(str, Enum):
    """Carrier status enum."""
    ACTIVE = "active"
    HIDDEN = "hidden"
    INACTIVE = "inactive"