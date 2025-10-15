"""Treatment Plan types and enums for Open Dental SDK."""

from enum import Enum


class TreatmentPlanStatus(str, Enum):
    """Treatment plan status enum."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SAVED = "saved"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class TreatmentPlanType(str, Enum):
    """Treatment plan type enum."""
    UNASSIGNED = "unassigned"
    INSURANCE = "insurance"
    DISCOUNT = "discount"
    PATIENT = "patient"


class AttachmentStatus(str, Enum):
    """Treatment plan attachment status enum."""
    ATTACHED = "attached"
    COMPLETED = "completed"
    SCHEDULED = "scheduled"
    CANCELLED = "cancelled"


class ProcedurePriority(str, Enum):
    """Treatment plan procedure priority enum."""
    IMMEDIATE = "immediate"
    URGENT = "urgent"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"
    OPTIONAL = "optional"