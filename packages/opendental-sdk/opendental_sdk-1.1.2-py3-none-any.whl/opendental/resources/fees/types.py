"""Fee types and enums for Open Dental SDK."""

from enum import Enum


class FeeScheduleType(str, Enum):
    """Fee schedule type enum."""
    STANDARD = "standard"
    ALLOWED = "allowed"
    USUAL = "usual"
    MEDICAID = "medicaid"
    CAPITATION = "capitation"
    PROVIDER_SPECIFIC = "provider_specific"
    CLINIC_SPECIFIC = "clinic_specific"


class FeeType(str, Enum):
    """Fee type enum."""
    STANDARD = "standard"
    PROVIDER_OVERRIDE = "provider_override"
    CLINIC_OVERRIDE = "clinic_override"
    INSURANCE_OVERRIDE = "insurance_override"