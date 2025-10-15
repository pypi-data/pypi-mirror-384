"""Appointment types types and enums for Open Dental SDK."""

from enum import Enum


class AppointmentTypeStatus(str, Enum):
    """Appointment type status enum."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class ProviderType(str, Enum):
    """Provider type enum."""
    DENTIST = "dentist"
    HYGIENIST = "hygienist"
    ASSISTANT = "assistant"
    SPECIALIST = "specialist"
    ANY = "any"


class OperatoryRequirement(str, Enum):
    """Operatory requirement enum."""
    STANDARD = "standard"
    SURGICAL = "surgical"
    HYGIENE = "hygiene"
    SPECIALTY = "specialty"
    ANY = "any"