"""Claims types and enums for Open Dental SDK."""

from enum import Enum


class ClaimType(str, Enum):
    """Claim type enum."""
    PRIMARY = "primary"
    SECONDARY = "secondary"
    PREAUTH = "preauth"
    CAPITATION = "capitation"
    OTHER = "other"


class ClaimStatus(str, Enum):
    """Claim status enum."""
    UNSENT = "unsent"
    SENT = "sent"
    RECEIVED = "received"
    WAITING = "waiting"
    SUPPLEMENTAL = "supplemental"
    PREAUTH = "preauth"
    HOLD = "hold"
    REJECTED = "rejected"


class Relationship(str, Enum):
    """Patient relationship to subscriber enum."""
    SELF = "self"
    SPOUSE = "spouse"
    CHILD = "child"
    OTHER = "other"


class AccidentType(str, Enum):
    """Accident type enum."""
    AUTO = "auto"
    EMPLOYMENT = "employment"
    OTHER = "other"


class PlaceOfService(str, Enum):
    """Place of service enum."""
    OFFICE = "11"  # Office
    HOME = "12"    # Home
    INPATIENT_HOSPITAL = "21"  # Inpatient Hospital
    OUTPATIENT_HOSPITAL = "22"  # Outpatient Hospital
    EMERGENCY_ROOM = "23"  # Emergency Room - Hospital
    AMBULATORY_SURGICAL_CENTER = "24"  # Ambulatory Surgical Center
    BIRTHING_CENTER = "25"  # Birthing Center
    MILITARY_TREATMENT = "26"  # Military Treatment Facility
    SKILLED_NURSING = "31"  # Skilled Nursing Facility
    NURSING_FACILITY = "32"  # Nursing Facility
    CUSTODIAL_CARE = "33"  # Custodial Care Facility
    HOSPICE = "34"  # Hospice
    AMBULANCE_LAND = "41"  # Ambulance - Land
    AMBULANCE_AIR = "42"  # Ambulance - Air or Water


class ClaimFrequency(str, Enum):
    """Claim frequency enum."""
    ORIGINAL = "1"  # Original
    CORRECTED = "7"  # Corrected/Replacement
    VOID = "8"  # Void