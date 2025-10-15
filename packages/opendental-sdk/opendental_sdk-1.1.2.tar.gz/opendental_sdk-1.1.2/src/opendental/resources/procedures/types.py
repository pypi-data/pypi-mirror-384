"""Procedure types and enums for Open Dental SDK."""

from enum import Enum


class ProcedureStatus(str, Enum):
    """Procedure status enum."""
    TREATMENT_PLANNED = "TP"
    COMPLETE = "C"
    EXISTING_CURRENT = "EC"
    EXISTING_OTHER = "EO"
    CONDITION = "Cn"
    DELETED = "D"
    REFERRED = "R"
    PREAUTH = "PA"


class ToothSurface(str, Enum):
    """Tooth surface enum."""
    MESIAL = "M"
    OCCLUSAL = "O"
    DISTAL = "D"
    BUCCAL = "B"
    LINGUAL = "L"
    INCISAL = "I"
    FACIAL = "F"


class ProcedurePriority(str, Enum):
    """Procedure priority enum."""
    LOW = "Low"
    NORMAL = "Normal"
    HIGH = "High"
    URGENT = "Urgent"


class BillType(str, Enum):
    """Bill type enum."""
    PRIMARY = "P"
    SECONDARY = "S"
    PATIENT = "Patient"
    CAPITATION = "Cap"